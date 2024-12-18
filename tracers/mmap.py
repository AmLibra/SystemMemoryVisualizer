from utils.tracker import MemoryTracker
from tracers.common import *

mmap_event_cache = dict()


def handle_mmap_enter_event(event):
    mmap_event_cache[event.pid_and_tid] = {
        "size": event.size,
        "comm": event.comm.decode("utf-8", "replace"),
    }
    if WITH_LOGGER:
        event_name = GREEN + "[sys_enter_mmap]" + END
        print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<39} | "
              f"PID: {event.pid_and_tid >>32:<6} | Requested Address: {hex(event.requested_addr):<18} | "
              f"Size (B): {event.size:<10}")


def handle_mmap_exit_event(event, tracker: MemoryTracker):
    if event.pid_and_tid not in mmap_event_cache:
        # this shouldn't happen?
        # it means that we missed an event because buffer was full!
        return

    mmap_info = mmap_event_cache[event.pid_and_tid]
    mmap_event_cache.pop(event.pid_and_tid)

    if event.actual_addr == 0xffffffffffffffff:
        # the allocation failed!
        return

    pid = event.pid_and_tid >> 32
    ts = event.timestamp
    tracker.add_allocation(pid, ts, event.actual_addr, mmap_info['size'], mmap_info['comm'])
    if WITH_LOGGER:
        resolved_name = GREEN + "[sys_exit_mmap]" + END
        print(f"\t{resolved_name} Process: {mmap_info['comm']:<32} | "
              f"PID: {pid:<6} | Size (B): {mmap_info['size']:<10} | "
              f"Actual Address: {hex(event.actual_addr):<30}\n")
