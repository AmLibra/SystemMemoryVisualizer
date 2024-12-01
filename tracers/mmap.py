from ctypes import cast, POINTER
from utils.tracker import MemoryTracker
from tracers.common import MmapEnterEvent, MmapExitEvent, GREEN, END, YELLOW, WITH_LOGGER


def handle_enter_event(cpu, raw_data, _size, tracker: MemoryTracker, target_pid, trace_all):
    event = cast(raw_data, POINTER(MmapEnterEvent)).contents
    if trace_all or event.pid == target_pid:
        if event.requested_addr == 0:
            tracker.mmap_event_cache_lock.acquire()
            tracker.mmap_event_cache[event.pid].append({
                "requested_addr": event.requested_addr,
                "size": event.size,
                "comm": event.comm.decode("utf-8", "replace"),
            })
            tracker.mmap_event_cache_lock.release()
            return
        tracker.add_allocation(event.pid, event.requested_addr, event.size, event.comm.decode("utf-8", "replace"))
        if WITH_LOGGER:
            event_name = GREEN + "[sys_enter_mmap]" + END
            print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<39} | "
                f"PID: {event.pid:<6} | Requested Address: {hex(event.requested_addr):<18} | "
                f"Size (B): {event.size:<10} | CPU: {cpu:<3}")

       

def handle_exit_event(cpu, raw_data, _size, tracker: MemoryTracker, target_pid, trace_all):
    event = cast(raw_data, POINTER(MmapExitEvent)).contents
    if trace_all or event.pid == target_pid:
        tracker.mmap_event_cache_lock.acquire()
        if event.pid in tracker.mmap_event_cache and tracker.mmap_event_cache[event.pid]:
            enter_data = tracker.mmap_event_cache[event.pid].pop(0)
            tracker.mmap_event_cache_lock.release()
            tracker.add_allocation(event.pid, event.actual_addr, enter_data['size'], enter_data['comm'])
            if WITH_LOGGER:
                event_name = YELLOW + "[sys_enter_mmap]" + END
                print(f"{event_name} Process: {enter_data['comm']:<40} | "
                    f"PID: {event.pid:<6} | Requested Address: {hex(enter_data['requested_addr']):<30} | "
                    f"Size (B): {enter_data['size']:<10} | CPU: {cpu:<3}")
                resolved_name = GREEN + "[mmap_resolved]" + END
                print(f"\t{resolved_name} Process: {enter_data['comm']:<32} | "
                    f"PID: {event.pid:<6} | "
                    f"Actual Address: {hex(event.actual_addr):<30}\n")
              
        else:
            tracker.mmap_event_cache_lock.release()
            