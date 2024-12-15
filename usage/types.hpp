#ifndef RSS_COMMON_HPP
#define RSS_COMMON_HPP

#include <sys/time.h>
#include <iostream>
extern "C" {

struct vma_info {
    uint64_t start_addr /* included */, end_addr /* excluded */;
    uint64_t rss;

    vma_info(uint64_t start_addr, uint64_t end_addr, uint64_t rss) :
        start_addr(start_addr), end_addr(end_addr),
        rss(rss) {}

/*
    struct page_range {
        uintptr_t start_page, end_page;

        page_range(uintptr_t start_page, uintptr_t end_page):
                start_page(start_page), end_page(end_page) {}
    };

    std::vector<page_range> present_segments;
*/


    bool operator==(const vma_info &other) const {
        return this->start_addr == other.start_addr &&
               this->end_addr == other.end_addr &&
               this->rss == other.rss;
    }

};

struct get_rss_retval {
    uint64_t timestamp;
    vma_info *data;
    size_t size;
    int return_code;
};

    /*
     * Return codes meaning:
     * -1 : number of pages that a process uses is too large (> 512TB)
     * -2 : error while reading pagemap - returned 0 or 01 before all the data has been read
     * -5 : line ocntaining Rss info (in smaps) couldn't be parsed
     */
}


void sleep_until(uint64_t next_start_time_nanos) {
    struct timeval now;
    gettimeofday(&now, NULL);

    // Get current time in milliseconds
    uint64_t current_time_nanos = now.tv_sec * 1000000000 + now.tv_usec*1000;

    // Calculate the sleep duration in seconds and microseconds
    if (next_start_time_nanos > current_time_nanos) {
        uint64_t sleep_duration_ns = next_start_time_nanos - current_time_nanos;

        std::cout << "sleeping for " << sleep_duration_ns << "ns" << std::endl;
        struct timespec sleep_time;
        sleep_time.tv_sec = sleep_duration_ns / 1000000000;
        sleep_time.tv_nsec = sleep_duration_ns % 1000000000;

        // Sleep until next_start_time_nanos
        nanosleep(&sleep_time, NULL);
    }
}

#define VMA_BUFF_SIZE (1000000 * sizeof(vma_info))

struct vma_info_array {
    vma_info* arr;
    size_t size = 0;

    vma_info_array(char* buff) : arr( (vma_info*) buff ){
    }

    void push_back(const vma_info& vma_info) {
        if (size == 1000000) exit(-10);
        arr[size] = vma_info;
        size++;
    }

    vma_info& operator[](size_t index) {
        if (index > 1000000 - 1) exit(-10);
        return arr[index];
    }
};


#endif //RSS_COMMON_HPP
