#include <fstream>
#include <chrono>
#include <iostream>
#include <vector>

#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#include "types.hpp"

/*
 * pagemap kernel ABI bits
 */
#define PM_ENTRY_BYTES      sizeof(uint64_t)
#define PM_STATUS_BITS      3
#define PM_STATUS_OFFSET    (64 - PM_STATUS_BITS)
#define PM_STATUS_MASK      (((1LL << PM_STATUS_BITS) - 1) << PM_STATUS_OFFSET)
#define PM_STATUS(nr)       (((nr) << PM_STATUS_OFFSET) & PM_STATUS_MASK)
#define PM_PSHIFT_BITS      6
#define PM_PSHIFT_OFFSET    (PM_STATUS_OFFSET - PM_PSHIFT_BITS)
#define PM_PSHIFT_MASK      (((1LL << PM_PSHIFT_BITS) - 1) << PM_PSHIFT_OFFSET)
#define PM_PSHIFT(x)        (((u64) (x) << PM_PSHIFT_OFFSET) & PM_PSHIFT_MASK)
#define PM_PFRAME_MASK      ((1LL << PM_PSHIFT_OFFSET) - 1)
#define PM_PFRAME(x)        ((x) & PM_PFRAME_MASK)

#define PM_PRESENT          PM_STATUS(4LL)
#define PM_SWAP             PM_STATUS(2LL)

#define PAGE_SIZE (uint64_t)(sysconf(_SC_PAGE_SIZE))
#define MAX_PAGE_NUM (~((uint64_t)(0ul)) / PAGE_SIZE)

// buffer can handle at most 2^27 entries,
// which corresponds to the virtual memory size of 2^39 (512TB)
#define BUFF_SIZE size_t(1 << 30)
char* buff;
char* vma_buff;

#define DEFAULT_PERIOD std::chrono::seconds(1)



//region maps

std::ifstream maps_file;

bool maps_open(pid_t pid) {
    char buf[30];

    snprintf(buf, 30, "/proc/%d/maps", pid);
    maps_file.open(buf, std::ifstream::binary);
    if (!maps_file) {
        perror("maps_open");
        return false;
    }

    return true;
}

void maps_close() {
    maps_file.close();
}

std::pair<uint64_t, vma_info_array> maps_read() {
    vma_info_array vmas(vma_buff);

    uint64_t total_vm_pages = 0;

    maps_file.clear();
    maps_file.seekg(0, std::ios::beg);
    for (std::string line; std::getline(maps_file, line);) {
        char* stopped;
        uintptr_t vma_start_addr = std::strtoul(line.data(), &stopped, 16);
        uintptr_t vma_end_addr = std::strtoul(stopped+1, nullptr, 16);

        vmas.push_back({vma_start_addr, vma_end_addr, 0});
        total_vm_pages += (vma_end_addr - vma_start_addr) / PAGE_SIZE;
    }
    return {total_vm_pages, vmas};
}

//endregion


//region pagemap

int pagemap_fd = 0;

bool pagemap_open(pid_t pid) {
    char buf[30];
    snprintf(buf, sizeof(buf), "/proc/%d/pagemap", pid);
    pagemap_fd = open(buf, O_RDONLY);
    if (pagemap_fd < 0) {
        perror("pagemap_open");
        return false;
    }

    return true;
}

void pagemap_close() {
    if (pagemap_fd > 0) {
        close(pagemap_fd);
    }
}

bool pagemap_read_vma(char *buf, unsigned long start_page, unsigned long page_cnt) {
    long bytes_to_read = page_cnt * sizeof(uint64_t);
    uint64_t nread = 0;
    while (nread < bytes_to_read) {
        uint64_t ret = pread(pagemap_fd, buf + nread, bytes_to_read - nread, start_page * sizeof(uint64_t) + nread);
        nread += ret;
        if (ret <= 0) {
            return false;
        }
    }

    return true;
}

bool pagemap_read_all_vmas(vma_info_array vmas) {
    char* cursor = buff;
    for (int i = 0; i < vmas.size; i++) {
        auto& vma = vmas[i];
        const auto start_page = vma.start_addr / PAGE_SIZE;
        const auto end_page = vma.end_addr / PAGE_SIZE;

        if (!pagemap_read_vma(cursor, start_page, end_page - start_page)) {
            return false;
        }

        cursor += (end_page - start_page) * sizeof(uint64_t);
    }

    return true;
}

//endregion


void page_table_walk_w_mapped_page_saving(uint64_t* entries, vma_info& vma) {

    const auto start_page = vma.start_addr / PAGE_SIZE;
    const auto end_page = vma.end_addr / PAGE_SIZE;
    uint64_t page_cnt = end_page - start_page;

    unsigned long total_pages_present = 0;
    uintptr_t continuous_segment_start_page = 0;
    bool is_prev_page_present = false;

    for (auto idx = 0; idx < page_cnt; idx++) {
        if (entries[idx] & PM_PRESENT) {

            if (!is_prev_page_present) {
                continuous_segment_start_page = start_page + idx;
            }

        } else if (is_prev_page_present) {
            auto continuous_segment_end_page = start_page + idx - 1;
            total_pages_present += continuous_segment_end_page - continuous_segment_start_page;
//            vma.present_segments.emplace_back(continuous_segment_start_page, continuous_segment_end_page);
        }

        is_prev_page_present = entries[idx] & PM_PRESENT;
    }

    if (is_prev_page_present) {
        auto continuous_segment_end_page = start_page - 1;
        total_pages_present += continuous_segment_end_page - continuous_segment_start_page;
//        vma.present_segments.emplace_back(continuous_segment_start_page, continuous_segment_end_page);
    }

    vma.rss = total_pages_present;
}

void page_table_walk(uint64_t* entries, vma_info& vma) {

    const auto start_page = vma.start_addr / PAGE_SIZE;
    const auto end_page = vma.end_addr / PAGE_SIZE;
    uint64_t page_cnt = end_page - start_page;

    unsigned long total_pages_present = 0;
    uintptr_t continuous_segment_start_page = 0;
    bool is_prev_page_present = false;

    for (auto idx = 0; idx < page_cnt; idx++) {
        if (entries[idx] & PM_PRESENT) {
            total_pages_present++;
        }
    }

    vma.rss = total_pages_present;
}

pid_t pid;
extern "C" {

int init(pid_t _pid) {
    pid = _pid;

    if (!pagemap_open(pid)) {
        return -1;
    }

    if (!maps_open(pid)) {
        return -2;
    }

    buff = (char*) mmap(NULL, BUFF_SIZE, PROT_READ | PROT_WRITE,
                        MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);

    if (buff == MAP_FAILED) {
        std::cerr<< "mmap failed" <<std::endl;
        perror("mmap failed");
        return -4;
    }

    vma_buff = (char*) mmap(NULL, VMA_BUFF_SIZE, PROT_READ | PROT_WRITE,
                        MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);

    if (vma_buff == MAP_FAILED) {
        std::cerr << "buffer allocation failed" <<std::endl;
        return -4;
    }

    return 0;
}



get_rss_retval get_rss(uint64_t next_start_time_nanos) {

    // sleep until next_start_time
    if (next_start_time_nanos != 0) {
        sleep_until(next_start_time_nanos);
    }

    // auto start = std::chrono::high_resolution_clock::now();

    auto [total_vm_pages, vmas] = maps_read();
    // check if the buffer is big enough
    if (total_vm_pages * sizeof(uint64_t) > BUFF_SIZE) {
        perror("vm too large!");
        return get_rss_retval{.return_code = -1};
    }

    if (!pagemap_read_all_vmas(vmas)) {
        return get_rss_retval{.return_code = -2};
    }

    struct timeval now;
    gettimeofday(&now, NULL);
    uint64_t read_end = now.tv_sec * 1000000000 + now.tv_usec * 1000;

    auto* cursor = reinterpret_cast<uint64_t *>(buff);
    for (int i = 0; i < vmas.size; i++) {
        auto& vma = vmas[i];
        page_table_walk(cursor, vma);
        cursor += (vma.end_addr - vma.start_addr) / PAGE_SIZE;
    }

    maps_close();
    // auto end = std::chrono::high_resolution_clock::now();

    return get_rss_retval{
        .timestamp = read_end,
        .data = vmas.arr,
        .size = vmas.size,
        .return_code = 0
    };
}

void deinit() {
    pagemap_close();
    maps_close();
    if (buff != nullptr) munmap(buff, BUFF_SIZE);
    if (vma_buff != nullptr) munmap(vma_buff, VMA_BUFF_SIZE);
}



}


int main(int argc, char* argv[]) {

    pid_t pid = std::stoi(argv[1]);

    if (auto ret = init(pid); ret != 0) {
        return ret;
    }

    auto rss_ret_val = get_rss(0);

    while (true) {

        auto next_wakeup = rss_ret_val.timestamp + DEFAULT_PERIOD.count();

        rss_ret_val = get_rss(next_wakeup);

        if (rss_ret_val.return_code != 0) {
            break;
        }
    }

    deinit();
    return 0;
}