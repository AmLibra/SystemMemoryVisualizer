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

    elif type == 10:  
        event = cast(raw_data, POINTER(Clone3EnterEvent)).contents
        handle_clone3_enter_events(event, tracked_pids, event_cache)

    elif type == 11:  
        event = cast(raw_data, POINTER(Clone3ExitEvent)).contents
        handle_clone3_exit_events(event, tracked_pids, tracker, event_cache)

    elif type == 12:  
        event = cast(raw_data, POINTER(VforkEnterEvent)).contents
        handle_vfork_enter_event(event, tracked_pids, event_cache)

    elif type == 13:  
        event = cast(raw_data, POINTER(VforkExitEvent)).contents
        handle_vfork_exit_event(event, tracked_pids, tracker, event_cache)

    else:
        print(f'size not recognized: {size}')


tracker_pid = 0

def set_tracker_pid(pid):
    global tracker_pid
    tracker_pid = pid

WITH_LOGGER = False

def debug_state(event_cache, tracked_pids):
    if not WITH_LOGGER:
        return
    print(f"DEBUG: tracked_pids: {tracked_pids}")
    print(f"DEBUG: event_cache.new_pids: {event_cache.new_pids}")
    print(f"DEBUG: event_cache.tracked_tids_that_cloned: {event_cache.tracked_tids_that_cloned}")

def handle_clone_enter_events(event, tracked_pids, event_cache: EventCache):
    pid = event.pid_and_tid >> 32

    # Only track events initiated by tracker_pid or its descendants
    if pid not in tracked_pids and pid != tracker_pid:
        return

    if WITH_LOGGER:
        print(f"Entering clone (pid={pid}, flags={event.flags})")
    if event.flags & 0x00010000 != 0:  # Skip threads (CLONE_THREAD)
        return

    event_cache.tracked_tids_that_cloned.add(event.pid_and_tid)
    debug_state(event_cache, tracked_pids)

def handle_clone_exit_events(event, tracked_pids: set, tracker: MemoryTracker, event_cache: EventCache):
    if event.pid_and_tid not in event_cache.tracked_tids_that_cloned:
        return

    pid = event.pid_and_tid >> 32
    if WITH_LOGGER:
        print(f"Exiting clone (pid={pid}, child_pid={event.child_pid})")

    # Add the child PID only if the parent is tracker_pid or a descendant
    if pid in tracked_pids or pid == tracker_pid:
        tracked_pids.add(event.child_pid)

    event_cache.tracked_tids_that_cloned.remove(event.pid_and_tid)
    debug_state(event_cache, tracked_pids)

def handle_clone3_enter_events(event, tracked_pids, event_cache: EventCache):
    pid = event.pid_and_tid >> 32

    if pid not in tracked_pids and pid != tracker_pid:
        return

    if WITH_LOGGER:
        print(f"Entering clone3 (pid={pid})")
    event_cache.tracked_tids_that_cloned.add(event.pid_and_tid)
    debug_state(event_cache, tracked_pids)

def handle_clone3_exit_events(event, tracked_pids: set, tracker: MemoryTracker, event_cache: EventCache):
    if event.pid_and_tid not in event_cache.tracked_tids_that_cloned:
        return

    pid = event.pid_and_tid >> 32
    if WITH_LOGGER:
        print(f"Exiting clone3 (pid={pid}, child_pid={event.child_pid})")

    if pid in tracked_pids or pid == tracker_pid:
        tracked_pids.add(event.child_pid)

    event_cache.tracked_tids_that_cloned.remove(event.pid_and_tid)
    debug_state(event_cache, tracked_pids)

def handle_vfork_enter_event(event, tracked_pids, event_cache: EventCache):
    pid = event.pid_and_tid >> 32

    if pid not in tracked_pids and pid != tracker_pid:
        return

    if WITH_LOGGER:
        print(f"Entering vfork (pid={pid})")
    event_cache.tracked_tids_that_cloned.add(event.pid_and_tid)
    debug_state(event_cache, tracked_pids)

def handle_vfork_exit_event(event, tracked_pids: set, tracker: MemoryTracker, event_cache: EventCache):
    if event.pid_and_tid not in event_cache.tracked_tids_that_cloned:
        return

    pid = event.pid_and_tid >> 32
    if WITH_LOGGER:
        print(f"Exiting vfork (pid={pid}, child_pid={event.child_pid})")

    if pid in tracked_pids or pid == tracker_pid:
        tracked_pids.add(event.child_pid)

    event_cache.tracked_tids_that_cloned.remove(event.pid_and_tid)
    debug_state(event_cache, tracked_pids)