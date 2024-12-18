from ctypes import Structure, c_ulonglong, c_char
from os import sysconf

WITH_LOGGER = False

PERF_BUFFER_SIZE_PAGES = 1024
PAGE_SIZE = sysconf("SC_PAGE_SIZE")
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
END = "\033[0m"


class Event(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
    ]

class MmapEnterEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("requested_addr", c_ulonglong),
        ("size", c_ulonglong),
        ("comm", c_char * 16),
    ]

class MmapExitEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("actual_addr", c_ulonglong),
    ]

class MunmapEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("start_addr", c_ulonglong),
        ("size", c_ulonglong),
        ("comm", c_char * 16),
    ]

MremapEnterEvent = 56
class MremapEnterEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("old_addr", c_ulonglong),
        ("old_size", c_ulonglong),
        ("new_addr", c_ulonglong),
        ("new_size", c_ulonglong),
        ("flags", c_ulonglong),
        ("comm", c_char * 16),
    ]

MremapExitEventSize = 18
class MremapExitEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("new_addr", c_ulonglong), # New address or -1 if failed: https://man7.org/linux/man-pages/man2/mremap.2.html
    ]

BrkEnterEventSize = 32
class BrkEnterEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("requested_brk", c_ulonglong),  # For enter events, requested break address
        ("comm", c_char * 16),
    ]

class BrkExitEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("actual_brk", c_ulonglong),  # For exit events, actual break address
        ("comm", c_char * 16),
    ]

class CloneEnterEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("flags", c_ulonglong),
        ("comm", c_char * 16),
    ]

class CloneExitEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("child_pid", c_ulonglong),
    ]

class Clone3EnterEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("flags", c_ulonglong),       # Clone flags
        ("pidfd", c_ulonglong),       # PID file descriptor
        ("child_tid", c_ulonglong),   # Child thread ID
        ("parent_tid", c_ulonglong),  # Parent thread ID
        ("comm", c_char * 16),        # Process name
    ]

class Clone3ExitEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("child_pid", c_ulonglong),  # PID of the child process
    ]

class VforkEnterEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("comm", c_char * 16),  # Process name
    ]

class VforkExitEvent(Structure):
    _fields_ = [
        ("type", c_ulonglong),
        ("pid_and_tid", c_ulonglong),
        ("timestamp", c_ulonglong),
        ("child_pid", c_ulonglong),  # PID of the child process
    ]