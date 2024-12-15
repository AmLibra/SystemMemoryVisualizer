from utils.tracker import MemoryTracker
from time import sleep


USAGE_INTERVAL = 1

def fetch_usage_loop(tracker: MemoryTracker, pid):
    try:
        while True:

            with open(f"/proc/{pid}/statm", "r") as file:
                fields = file.readline().strip().split()

            print(fields)
            # statm format: [size] [resident] [shared] [text] [lib] [data] [dt]
            vm = int(fields[0])  # Virtual memory size
            rss = int(fields[1])  # Resident Set Size

            tracker.send_usage(pid, rss, vm)

            sleep(USAGE_INTERVAL)

    except FileNotFoundError:
        pass
