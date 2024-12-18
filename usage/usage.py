import threading
from utils.tracker import MemoryTracker
from time import sleep
import os
import time

USAGE_INTERVAL = 1


def parse_statm(pid):
    try:
        with open(f"/proc/{pid}/statm", "r") as file:
            fields = file.readline().strip().split()

        # statm format: [size] [resident] [shared] [text] [lib] [data] [dt]
        return int(fields[0]), int(fields[1])  # Virtual memory size

    except (FileNotFoundError, PermissionError):
        return 0, 0

    return 0, 0



def fetch_usage_loop(tracker: MemoryTracker, target_pids_lock: threading.Lock, target_pids: set):
    t = time.time()
    while True:
        vm, rss = 0, 0

        with target_pids_lock:
            target_pids_local = target_pids.copy()

        for pid in target_pids_local:
            _vm, _rss = parse_statm(pid)
            if _vm == 0 and time.time() - t > 0.5:
                tracker.clear_allocations_for_pid(pid) # wait for 0.5 seconds so that measurements are stable, otherwise will clear allocations at the start
            vm += _vm
            rss += _rss

        tracker.send_usage(rss, vm)
        sleep(USAGE_INTERVAL)


def fetch_total_usage_loop(tracker: MemoryTracker):
    while True:
        vm, rss = 0, 0

        for entry in os.listdir('/proc'):
            if entry.isnumeric():  # Check if the directory name is a PID
                _vm, _rss = parse_statm(entry)
                vm += _vm
                rss += _rss

        tracker.send_usage(rss, vm)
        sleep(USAGE_INTERVAL)
