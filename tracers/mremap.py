from utils.tracker import MemoryTracker
from tracers.common import *

mremap_event_cache = dict()


def handle_mremap_enter_event(event):
    mremap_event_cache[event.pid_and_tid] = {
        "old_addr": event.old_addr,  # align to page
        "old_size": event.old_size,  # can be 0!!!, if 0
        "new_size": event.new_size,
        "new_addr": event.new_addr,
        "unmap_old": False if event.flags & 1 != 0 and event.flags & 4 != 0 else True,
        "unmap_new": True if event.flags & 1 != 0 and event.flags & 4 == 0 else False,
        "comm": event.comm.decode("utf-8", "replace"),
    }

    # if event.flags & 1 == 0:
    # # MREMAP_MAYMOVE is not set
    #     mremap_info["unmap_old"] = True
    #     mremap_info["unmap_new"] = False
    # elif event.flags & 1 == 0 and event.flags & 2 == 0:
    # # only MREMAP_MAYMOVE is set
    #     mremap_info["unmap_old"] = True
    #     mremap_info["unmap_new"] = True
    # else:
    #     if event.flags & 2 != 0:
    #         # MREMAP_MAYMOVE and MREMAP_FIXED is set
    #         mremap_info["unmap_new"] = True
    #
    #     elif event.flags & 4 != 0:
    #         # MREMAP_MAYMOVE and MREMAP_DONTUNMAP is set
    #         mremap_info["unmap_old"] = False

    if WITH_LOGGER:
        event_name = YELLOW + "[sys_enter_mremap]" + END
        print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<30} | "
              f"PID: {event.pid_and_tid >> 32:<6} | Old Addr: {hex(event.old_addr):<18} | "
              f"Old Size: {event.old_size:<10} | New Size: {event.new_size:<10} | "
              f"New Addr: {hex(event.new_addr):<18}")


def handle_mremap_exit_event(event, tracker: MemoryTracker):
    pid = event.pid_and_tid >> 32

    if event.pid_and_tid not in mremap_event_cache:
        # this shouldn't happen?
        # it means that we missed an event because buffer was full!
        return

    mremap_info = mremap_event_cache[event.pid_and_tid]
    mremap_event_cache.pop(event.pid_and_tid)

    if event.new_addr != 0xffffffffffffffff:  # successful mremap, move the allocation and no need to log
        ts = event.timestamp
        if mremap_info['unmap_old']:
            tracker.remove_allocation(pid, ts, mremap_info['old_addr'],
                                      mremap_info['old_size'])  # old size can be 0!, must be done

        if mremap_info['unmap_new'] and mremap_info['new_addr'] != 0:
            tracker.remove_allocation(pid, ts, mremap_info['new_addr'],
                                      mremap_info['new_size'])  # maybe there;s no alloc so don't force

        tracker.add_allocation(pid, ts, event.new_addr, mremap_info['new_size'], mremap_info['comm'])

        if WITH_LOGGER:
            event_name = YELLOW + "[sys_exit_mremap]" + END
            print(f"{event_name} Process: {mremap_info['comm']:<30} | "
                  f"PID: {pid:<6} | New Address : {hex(event.new_addr):<18} | New Size: {mremap_info['new_size']:<10}")
    else:
        if WITH_LOGGER:
            event_name = RED + "[sys_exit_mremap]" + END
            print(
                f"{event_name} ERROR: Failed to remap the allocation for process {mremap_info['comm']} with PID {pid}")
