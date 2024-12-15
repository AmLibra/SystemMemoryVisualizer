from ctypes import cast, POINTER
from utils.tracker import MemoryTracker
from tracers.common import MremapEnterEvent, MremapExitEvent, YELLOW, END, WITH_LOGGER, RED

def handle_mremap_enter(cpu, raw_data, _size, tracker: MemoryTracker, target_pids, trace_all):
    event = cast(raw_data, POINTER(MremapEnterEvent)).contents
    if trace_all or event.pid in target_pids:
        tracker.mremap_event_cache_lock.acquire()
        # simply cache the mremap event while waiting for the exit event
        tracker.mremap_event_cache[event.pid].append({
            "old_addr": event.old_addr,
            "old_size": event.old_size,
            "new_size": event.new_size,
            "new_addr": event.new_addr, # optional, used to move the allocation
            "comm": event.comm.decode("utf-8", "replace"),
        })
        tracker.mremap_event_cache_lock.release()

        if WITH_LOGGER:
            event_name = YELLOW + "[sys_enter_mremap]" + END
            print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<30} | "
                  f"PID: {event.pid:<6} | Old Addr: {hex(event.old_addr):<18} | "
                  f"Old Size: {event.old_size:<10} | New Size: {event.new_size:<10} | "
                  f"New Addr: {hex(event.new_addr):<18} | CPU: {cpu:<3}") 


def handle_mremap_exit(cpu, raw_data, _size, tracker: MemoryTracker, target_pids, trace_all):
    event = cast(raw_data, POINTER(MremapExitEvent)).contents
    if trace_all or event.pid in target_pids:
        tracker.mremap_event_cache_lock.acquire()
        if event.pid in tracker.mremap_event_cache and tracker.mremap_event_cache[event.pid]:
            enter_data = tracker.mremap_event_cache[event.pid].pop(0)
            tracker.mremap_event_cache_lock.release()
            ret_value = event.new_addr
            if ret_value != -1: # successful mremap, move the allocation and no need to log
                tracker.remove_allocation(event.pid, enter_data['old_addr'], enter_data['old_size'])
                tracker.add_allocation(event.pid, ret_value, enter_data['new_size'], enter_data['comm'])
                if WITH_LOGGER:
                    event_name = YELLOW + "[sys_exit_mremap]" + END
                    print(f"{event_name} Process: {enter_data['comm']:<30} | "
                          f"PID: {event.pid:<6} | New Address : {hex(ret_value):<18} | New Size: {enter_data['new_size']:<10}")
            else:
                if WITH_LOGGER:
                    event_name = RED + "[sys_exit_mremap]" + END
                    print(f"{event_name} ERROR: Failed to remap the allocation for process {enter_data['comm']} with PID {event.pid}")
        else:
            tracker.mremap_event_cache_lock.release()

            