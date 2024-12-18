from utils.tracker import MemoryTracker
from tracers.common import RED, END, WITH_LOGGER

mremap_event_cache = dict()


def handle_munmap_exit_event(event, tracker: MemoryTracker):
    ts = event.timestamp
    tracker.remove_allocation(event.pid_and_tid >> 32, ts, event.start_addr, event.size)
    if WITH_LOGGER:
        event_name = RED + "[sys_munmap]" + END
        print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<38} | "
              f"PID: {event.pid_and_tid >> 32:<6} | Address: {hex(event.start_addr):<18} | "
              f"Size (B): {event.size:<10}")
