from ctypes import cast, POINTER
from utils.tracker import MemoryTracker
from tracers.common import MunmapEvent
from tracers.common import RED, END, WITH_LOGGER

def handle_munmap(cpu, raw_data, _size, tracker: MemoryTracker, target_pid, trace_all):
    event = cast(raw_data, POINTER(MunmapEvent)).contents
    if trace_all or event.pid == target_pid:
        tracker.remove_allocation(event.pid, event.start_addr, event.size)
        if WITH_LOGGER:
            event_name = RED + "[sys_munmap]" + END
            print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<38} | "
                f"PID: {event.pid:<6} | Address: {hex(event.start_addr):<18} | "
                f"Size (B): {event.size:<10} | CPU: {cpu:<3}")