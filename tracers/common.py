from ctypes import Structure, c_ulonglong, c_char
from os import sysconf

WITH_LOGGER = False

PERF_BUFFER_SIZE_PAGES = 128
PAGE_SIZE = sysconf("SC_PAGE_SIZE")
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
END = "\033[0m"


MmapEnterEventSize = 40
class MmapEnterEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("requested_addr", c_ulonglong),
        ("size", c_ulonglong),
        ("comm", c_char * 16),
    ]

MmapExitEventSize = 16
class MmapExitEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("actual_addr", c_ulonglong),
    ]

MunmapEventSize = 40
class MunmapEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("start_addr", c_ulonglong),
        ("size", c_ulonglong),
        ("comm", c_char * 16),
    ]

MremapEnterEvent = 56
class MremapEnterEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("old_addr", c_ulonglong),
        ("old_size", c_ulonglong),
        ("new_addr", c_ulonglong),
        ("new_size", c_ulonglong),
        ("comm", c_char * 16),
    ]

MremapExitEventSize = 16
class MremapExitEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("new_addr", c_ulonglong), # New address or -1 if failed: https://man7.org/linux/man-pages/man2/mremap.2.html
    ]

BrkEnterEventSize = 32
class BrkEnterEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("requested_brk", c_ulonglong),  # For enter events, requested break address
        ("comm", c_char * 16),
    ]

BrkExitEventSize = 33
class BrkExitEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("actual_brk", c_ulonglong),  # For exit events, actual break address
        ("comm", c_char * 16),
        ("dummy", c_char)
    ]

CloneEnterEventSize = 64
class CloneEnterEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("flags", c_ulonglong),
        ("newsp", c_ulonglong),
        ("parent_tid", c_ulonglong),  # For exit events, actual break address
        ("child_tid", c_ulonglong),  # For exit events, actual break address
        ("tls", c_ulonglong),  # For exit events, actual break address
        ("comm", c_char * 16),
    ]

CloneExitEventSize = 17
class CloneExitEvent(Structure):
    _fields_ = [
        ("pid_and_tid", c_ulonglong),
        ("child_pid", c_ulonglong),
        ("dummy", c_char)
    ]
