from utils.tracker import MemoryTracker
from tracers.common import WITH_LOGGER, YELLOW, END


def handle_brk_enter_event(event):
    if WITH_LOGGER:
        event_name = YELLOW + "[sys_enter_brk]" + END
        print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<20} | "
              f"PID: {event.pid_and_tid >> 32:<6} | Requested Break: {hex(event.requested_brk):<18}")


def handle_brk_exit_event(event, tracker: MemoryTracker):
    pid, tid = event.pid_and_tid >> 32, event.pid_and_tid & 0xffffffff
    ts = event.timestamp
    tracker.handle_brk(pid, ts, tid, event.actual_brk, event.comm.decode("utf-8", "replace"))
    if WITH_LOGGER:
        event_name = YELLOW + "[sys_exit_brk]" + END
        print(f"{event_name} Process: {event.comm.decode('utf-8', 'replace'):<20} | "
              f"PID: {pid:<6} | Actual Break: {hex(event.actual_brk):<18}")
