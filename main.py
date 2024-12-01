#!/usr/bin/python3

import sys
from bcc import BPF
from utils.tracker import MemoryTracker, SUMMARY_INTERVAL
from tracers.mmap import handle_enter_event, handle_exit_event
from tracers.munmap import handle_munmap
from tracers.mremap import handle_mremap_enter, handle_mremap_exit
from tracers.brk import handle_brk_enter_event, handle_brk_exit_event
from utils.runner import Runner
from tracers.common import PAGE_SIZE
import threading

# Initialize Runner
runner = Runner()
tracker = MemoryTracker(PAGE_SIZE)

if len(sys.argv) < 2:
    print("Usage: sudo ./main.py <command | all>")
    sys.exit(1)

print(f"Page size: {PAGE_SIZE} bytes")
print("Initializing BPF programs...")

bpf_mmap = BPF(src_file="mmap/trace_mmap.c")
print("\t Loaded mmap BPF program successfully")

bpf_munmap = BPF(src_file="munmap/trace_munmap.c")
print("\t Loaded munmap BPF program successfully")

bpf_mremap = BPF(src_file="mremap/trace_mremap.c")
print("\t Loaded mremap BPF program successfully")

bpf_brk = BPF(src_file="brk/trace_brk.c")

# Attach tracepoints
print("Attaching tracepoints...")
bpf_mmap.attach_tracepoint(tp="syscalls:sys_enter_mmap", fn_name="trace_mmap_enter")
print("\t Attached to sys_enter_mmap")
bpf_mmap.attach_tracepoint(tp="syscalls:sys_exit_mmap", fn_name="trace_mmap_exit")
print("\t Attached to sys_exit_mmap")
bpf_munmap.attach_tracepoint(tp="syscalls:sys_enter_munmap", fn_name="trace_munmap")
print("\t Attached to sys_enter_munmap")
bpf_mremap.attach_tracepoint(tp="syscalls:sys_enter_mremap", fn_name="trace_mremap_enter")
print("\t Attached to sys_enter_mremap")
bpf_mremap.attach_tracepoint(tp="syscalls:sys_exit_mremap", fn_name="trace_mremap_exit")
print("\t Attached to sys_exit_mremap")
bpf_brk.attach_tracepoint(tp="syscalls:sys_enter_brk", fn_name="trace_brk_enter")
print("\t Attached to sys_enter_brk")
bpf_brk.attach_tracepoint(tp="syscalls:sys_exit_brk", fn_name="trace_brk_exit")
print("\t Attached to sys_exit_brk")

trace_all = False
target_pid = None
command = sys.argv[1:]
if command[0] == "all":
    print("Tracing all mmap events...")
    trace_all = True
else:
    print(f"Running command: {command}")
    target_pid = runner.run_command(command)  # Start the command and get its PID
    print(f"Tracing mmap events for PID {target_pid}... Ctrl-C to stop.")

bpf_mmap["mmap_enter_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_enter_event(cpu, raw_data, size, tracker, target_pid, trace_all)
)
bpf_mmap["mmap_exit_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_exit_event(cpu, raw_data, size, tracker, target_pid, trace_all)
)
bpf_munmap["munmap_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_munmap(cpu, raw_data, size, tracker, target_pid, trace_all)
)
bpf_mremap["mremap_enter_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_mremap_enter(cpu, raw_data, size, tracker, target_pid, trace_all)
)
bpf_mremap["mremap_exit_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_mremap_exit(cpu, raw_data, size, tracker, target_pid, trace_all)
)
bpf_brk["brk_enter_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_brk_enter_event(cpu, raw_data, size, tracker, target_pid, trace_all)
)
bpf_brk["brk_exit_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_brk_exit_event(cpu, raw_data, size, tracker, target_pid, trace_all)
)

# Start the summary thread
print(f"Starting summary thread with sleep interval of {SUMMARY_INTERVAL} seconds")
summary_thread = threading.Thread(target=tracker.summarize_allocations_loop, daemon=True)
summary_thread.start()
print("Started summary thread")

print("Tracing mmap events... Ctrl-C to stop.")

# Handle exit and cleanup
try:
    while True:
        bpf_mmap.perf_buffer_poll(timeout=100)
        bpf_munmap.perf_buffer_poll(timeout=100)
        bpf_mremap.perf_buffer_poll(timeout=100)
        bpf_brk.perf_buffer_poll(timeout=100)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    runner.cleanup()
