#include <chrono>
#include <iostream>
#include <vector>
#include <string>

#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/time.h>

#include "types.hpp"

#define BUFF_SIZE size_t(1 << 27)


int smaps_fd = 0;
char* buff;
char* vma_buff;


/** smaps record format:
bb79cf130000-bb79cf131000 r-xp 00000000 fc:00 1886752                    /home/pavle/eeee/test
Size:                  4 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Rss:                   4 kB
Pss:                   4 kB
Pss_Dirty:             0 kB
Shared_Clean:          0 kB
Shared_Dirty:          0 kB
Private_Clean:         4 kB
Private_Dirty:         0 kB
Referenced:            4 kB
Anonymous:             0 kB
KSM:                   0 kB
LazyFree:              0 kB
AnonHugePages:         0 kB
ShmemPmdMapped:        0 kB
FilePmdMapped:         0 kB
Shared_Hugetlb:        0 kB
Private_Hugetlb:       0 kB
Swap:                  0 kB
SwapPss:               0 kB
Locked:                0 kB
THPeligible:           0
VmFlags: rd ex mr mw me
 */

uint64_t smaps_read() {

    // auto start = std::chrono::high_resolution_clock::now();

    char* dest = buff;
    ssize_t read = 0, total_read = 0;
    while ((read = pread(smaps_fd, dest, BUFF_SIZE - total_read, total_read)) > 0) {
        // warn always reads less than 4096 !!!!!
         std::cout << "read " << read << " ";
        total_read += read;
        dest += read;
    }
    // std::cout << std::endl << read << std::endl;
    return total_read;


    // auto end = std::chrono::high_resolution_clock::now();
    // auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // std::cout << duration.count() << std::endl;
    // std::cout<< "bytes read: "<< bytes_read << std::endl;

}

std::pair<int, vma_info_array> parse_smaps(uint64_t bytes_read) {
    std::string_view data_stream(buff, bytes_read);

    vma_info_array vmas(vma_buff);

    size_t start = 0;
    size_t end = data_stream.find('\n');

    while (end != std::string_view::npos) {
        auto line = data_stream.substr(start, end - start);
        data_stream = data_stream.substr(end + 1);

        char* stopped;
        uintptr_t start_addr = std::strtoul(line.data(), &stopped, 16);
        uintptr_t end_addr = std::strtoul(stopped+1, nullptr, 16);

        for (int i = 0; i < 3; i++) data_stream = data_stream.substr(data_stream.find('\n') + 1);

        char unit;
        uint64_t rss;

        if (sscanf(data_stream.data()+4,  "%ld %c", &rss, &unit) != 2) {
            return {-5, vmas};
        }

        switch (unit) {
        case 'G': case 'g':
            rss <<= 10;
        case 'M': case 'm':
            rss <<= 10;
        case 'K': case 'k':
            rss <<= 10;
        }

        for (int i = 0; i < 21; i++) data_stream = data_stream.substr(data_stream.find('\n') + 1);

        vmas.push_back({start_addr, end_addr, rss});
        end = data_stream.find('\n');
    }

    return {0, vmas};
}

extern "C" {

char buf[30];

int init(pid_t pid) {

    snprintf(buf, sizeof(buf), "/proc/%d/smaps", pid);


    buff = (char*) mmap(NULL, BUFF_SIZE, PROT_READ | PROT_WRITE,
                        MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);

    if (buff == MAP_FAILED) {
        std::cerr << "buffer allocation failed" <<std::endl;
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

    smaps_fd = open(buf, O_RDONLY);
    if (smaps_fd < 0) {
        std::cerr << "smaps file couldn't be opened" << std::endl;

        struct timeval now;
        gettimeofday(&now, NULL);
        uint64_t read_end = now.tv_sec * 1000000000 + now.tv_usec * 1000;



        return get_rss_retval{
            .timestamp = read_end,
            .data = nullptr,
            .size = 0,
            .return_code = -3,
        };
    }

    // sleep until next_start_time
    if (next_start_time_nanos != 0) {
        sleep_until(next_start_time_nanos);
    }

    auto bytes_read = smaps_read();

    struct timeval now;
    gettimeofday(&now, NULL);
    uint64_t read_end = now.tv_sec * 1000000000 + now.tv_usec * 1000;


    auto [ret_val, vmas] = parse_smaps(bytes_read);

    close(smaps_fd);

    return get_rss_retval{
        .timestamp = read_end,
        .data = vmas.arr,
        .size = vmas.size,
        .return_code = ret_val,
    };
}

void deinit() {
    if (smaps_fd != 0) close(smaps_fd);
    if (buff != nullptr) munmap(buff, BUFF_SIZE);
    if (vma_buff != nullptr) munmap(vma_buff, VMA_BUFF_SIZE);
}

}
