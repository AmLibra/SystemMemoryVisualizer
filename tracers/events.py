from ctypes import cast, POINTER

from tracers.brk import handle_brk_enter_event, handle_brk_exit_event
from tracers.event_cache import EventCache
from tracers.mmap import *
from tracers.mremap import *
from tracers.munmap import handle_munmap_exit_event
from utils.tracker import MemoryTracker


def handle_event(cpu, raw_data, size, tracker: MemoryTracker, tracked_pids, event_cache=None):
    event = cast(raw_data, POINTER(Event)).contents
    type = event.type
    pid = event.pid_and_tid >> 32

    if type == 1:
        event = cast(raw_data, POINTER(MmapEnterEvent)).contents
        if pid in tracked_pids:
            handle_mmap_enter_event(event)
        elif event_cache is not None and event_cache.should_cache():
            event_cache.add(pid, cpu, raw_data, size)

    elif type == 2:
        event = cast(raw_data, POINTER(MmapExitEvent)).contents
        if pid in tracked_pids:
            handle_mmap_exit_event(event, tracker)
        elif event_cache is not None and event_cache.should_cache():
            event_cache.add(pid, cpu, raw_data, size)

    elif type == 3:
        event = cast(raw_data, POINTER(MremapEnterEvent)).contents
        if pid in tracked_pids:
            handle_mremap_enter_event(event)
        elif event_cache is not None and event_cache.should_cache():
            event_cache.add(pid, cpu, raw_data, size)

    elif type == 4:
        event = cast(raw_data, POINTER(MremapExitEvent)).contents
        if pid in tracked_pids:
            handle_mremap_exit_event(event, tracker)
        elif event_cache is not None and event_cache.should_cache():
            event_cache.add(pid, cpu, raw_data, size)

    elif type == 5:
        event = cast(raw_data, POINTER(MunmapEvent)).contents
        if pid in tracked_pids:
            handle_munmap_exit_event(event, tracker)
        elif event_cache is not None and event_cache.should_cache():
            event_cache.add(pid, cpu, raw_data, size)

    elif type == 6:
        event = cast(raw_data, POINTER(BrkEnterEvent)).contents
        if pid in tracked_pids:
            handle_brk_enter_event(event)
        # elif event_cache.should_cache():
        #     event_cache.add(cpu, raw_data, size)

    elif type == 7:
        event = cast(raw_data, POINTER(BrkExitEvent)).contents
        if pid in tracked_pids:
            handle_brk_exit_event(event, tracker)
        elif event_cache is not None and event_cache.should_cache():
            event_cache.add(pid, cpu, raw_data, size)

    elif type == 8:
        event = cast(raw_data, POINTER(CloneEnterEvent)).contents
        handle_clone_enter_events(event, tracked_pids, event_cache)

    elif type == 9:
        event = cast(raw_data, POINTER(CloneExitEvent)).contents
        handle_clone_exit_events(event, tracked_pids, tracker, event_cache)

    else:
        print(f'size not recognized: {size}')


tracker_pid = 0

def set_tracker_pid(pid):
    global tracker_pid
    tracker_pid = pid

def handle_clone_enter_events(event, tracked_pids, event_cache: EventCache):
    global tracker_pid

    pid = event.pid_and_tid >> 32
    # print(f'entering clone {pid}')
    if event.flags & 0x00010000 != 0:
        # CLONE_THREAD set
        # print(f'CLONE_THREAD set')
        pass

    # print(f'len(event_cache.tracked_tids_that_cloned) > 0 or pid in tracked_pids:{len(event_cache.tracked_tids_that_cloned) > 0 or pid in tracked_pids}')
    if len(event_cache.tracked_tids_that_cloned) > 0 or pid in tracked_pids or (tracker_pid is not None and pid == tracker_pid):
        tracker_pid = None
        event_cache.tracked_tids_that_cloned.add(event.pid_and_tid)


def handle_clone_exit_events(event, tracked_pids: set, tracker: MemoryTracker, event_cache: EventCache):
    # all events should be cached from now on!
    # add the new pid to tracked pids

    if event.pid_and_tid not in event_cache.tracked_tids_that_cloned:
        return

    pid = event.pid_and_tid >> 32
    # print(f'exiting clone {pid} -> {event.child_pid}')

    if event.child_pid in tracked_pids:
        return

    event_cache.new_pids.add(event.child_pid)
    event_cache.tracked_tids_that_cloned.remove(event.pid_and_tid)
    # print(f'len is {len(event_cache.tracked_tids_that_cloned)}')
    if len(event_cache.tracked_tids_that_cloned) == 0:

        for pid in event_cache.new_pids:
            for (cpu, raw_data, size) in event_cache.cached_events[pid]:
                handle_event(cpu, raw_data, size, tracker, event_cache.new_pids, None)

        if event_cache.first:
            event_cache.first = False
            tracked_pids.clear()

        tracked_pids.update(event_cache.new_pids)
        event_cache.cached_events.clear()
        event_cache.new_pids.clear()
