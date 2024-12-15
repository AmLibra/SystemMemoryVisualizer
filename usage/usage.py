import threading
from utils.tracker import MemoryTracker
from time import sleep


USAGE_INTERVAL = 1

def fetch_usage_loop(tracker: MemoryTracker, target_pids_lock: threading.Lock, target_pids: set):
    while True:
        vm, rss = 0, 0

        with target_pids_lock:
            target_pids_local = target_pids.copy()

        if len(target_pids_local) == 0:
            break
            
        for pid in target_pids_local:
            try:
                with open(f"/proc/{pid}/statm", "r") as file:
                    fields = file.readline().strip().split()

                # statm format: [size] [resident] [shared] [text] [lib] [data] [dt]
                vm += int(fields[0])  # Virtual memory size
                rss += int(fields[1])  # Resident Set Size

            except FileNotFoundError:
                pass

        tracker.send_usage(rss, vm)

        sleep(USAGE_INTERVAL)

