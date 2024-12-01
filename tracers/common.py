from ctypes import Structure, c_ulonglong, c_char
from os import sysconf

WITH_LOGGER = True

PAGE_SIZE = sysconf("SC_PAGE_SIZE")
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
END = "\033[0m"

class MmapEnterEvent(Structure):
    _fields_ = [
        ("pid", c_ulonglong),
        ("requested_addr", c_ulonglong),
        ("size", c_ulonglong),
        ("comm", c_char * 16),
    ]

class MmapExitEvent(Structure):
    _fields_ = [
        ("pid", c_ulonglong),
        ("actual_addr", c_ulonglong),
    ]

class MunmapEvent(Structure):
    _fields_ = [
        ("pid", c_ulonglong),
        ("start_addr", c_ulonglong),
        ("size", c_ulonglong),
        ("comm", c_char * 16),
    ]

class MremapEnterEvent(Structure):
    _fields_ = [
        ("pid", c_ulonglong),
        ("old_addr", c_ulonglong),
        ("old_size", c_ulonglong),
        ("new_addr", c_ulonglong),
        ("new_size", c_ulonglong),
        ("comm", c_char * 16),
    ]

class MremapExitEvent(Structure):
    _fields_ = [
        ("pid", c_ulonglong),
        ("new_addr", c_ulonglong), # New address or -1 if failed: https://man7.org/linux/man-pages/man2/mremap.2.html
    ]

class BrkEnterEvent(Structure):
    _fields_ = [
        ("pid", c_ulonglong),
        ("tid", c_ulonglong),
        ("requested_brk", c_ulonglong),  # For enter events, requested break address
        ("comm", c_char * 16),
    ]

class BrkExitEvent(Structure):
    _fields_ = [
        ("pid", c_ulonglong),
        ("tid", c_ulonglong),
        ("actual_brk", c_ulonglong),  # For exit events, actual break address
        ("comm", c_char * 16),
    ]
