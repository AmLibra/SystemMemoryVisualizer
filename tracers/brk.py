from ctypes import cast, POINTER
from tracers.common import BrkEnterEvent, BrkExitEvent
from utils.tracker import MemoryTracker
from tracers.common import WITH_LOGGER, YELLOW, END



def handle_brk_enter_event(cpu, raw_data, size, tracker: MemoryTracker, target_pid, trace_all):
    event = cast(raw_data, POINTER(BrkEnterEvent)).contents
    if trace_all or event.pid == target_pid:
        if WITH_LOGGER:
            event_name =  YELLOW + "[sys_enter_brk]" + END
            print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<20} | "
                f"PID: {event.pid:<6} | Requested Break: {hex(event.requested_brk):<18} | CPU: {cpu:<3}")
      

def handle_brk_exit_event(cpu, raw_data, size, tracker: MemoryTracker, target_pid, trace_all):
    event = cast(raw_data, POINTER(BrkExitEvent)).contents
    if trace_all or event.pid == target_pid:    
        tracker.handle_brk(event.pid, event.tid, event.actual_brk, event.comm.decode("utf-8", "replace"))
        if WITH_LOGGER:
            event_name = YELLOW + "[sys_exit_brk]" + END
            print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<20} | "
                f"PID: {event.pid:<6} | Actual Break: {hex(event.actual_brk):<18} | CPU: {cpu:<3}")