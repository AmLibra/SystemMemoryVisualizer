from ctypes import CDLL, Structure, c_uint64, POINTER, c_size_t, c_int
from utils.tracker import MemoryTracker
import os
from time import sleep

RSS_LIB_NAME = os.path.dirname(os.path.realpath(__file__)) + '/librss.so'
RSS_INTERVAL = 1  # milliseconds


class VmaInfo(Structure):
    _fields_ = [
        ("start_addr", c_uint64),
        ("end_addr", c_uint64),
        ("rss", c_uint64),
    ]


class GetRssRetval(Structure):
    _fields_ = [
        ("timestamp", c_uint64),
        ("data", POINTER(VmaInfo)),
        ("size", c_size_t),
        ("return_code", c_int)
    ]


def fetch_rss_native_loop(tracker: MemoryTracker, pid):
    rsslib = CDLL(RSS_LIB_NAME)
    rsslib.init.restype = c_int
    rsslib.get_rss.restype = GetRssRetval
    rsslib.get_rss.argtypes = [c_uint64]

    result = rsslib.init(pid)
    if result != 0:
        print(f'rss thread failed in init, errcode {result}')

    next_start_time = 0  # read immediately
    while True:
        result = rsslib.get_rss(next_start_time)  # sleeps until the start time

        if result.return_code != 0:
            print(f'rss thread failed in get_rss, errcode {result}')

        next_start_time = result.timestamp + RSS_INTERVAL * 1_000_000

        vma_info_list = [
            {
                "start_addr": result.data[i].start_addr,
                "end_addr": result.data[i].end_addr,
                "rss": result.data[i].rss,
            }
            for i in range(result.size)]

        tracker.add_rss_info(pid, result.timestamp, vma_info_list)
