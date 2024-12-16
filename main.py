#!/usr/bin/python3

import sys
from bcc import BPF
from utils.tracker import MemoryTracker, SUMMARY_INTERVAL
from usage.usage import USAGE_INTERVAL, fetch_usage_loop
from tracers.mmap import handle_enter_event, handle_exit_event
from tracers.munmap import handle_munmap
from tracers.mremap import handle_mremap_enter, handle_mremap_exit
from tracers.brk import handle_brk_enter_event, handle_brk_exit_event
from utils.runner import Runner
from tracers.common import PAGE_SIZE
import threading
import time
import subprocess
import os
import signal
import re

# Global target_pids set to track live updates
target_pids = set()
target_pids_lock = threading.Lock()

# Initialize Runner
runner = Runner()
# Initialize MemoryTracker
tracker = MemoryTracker(PAGE_SIZE)

def monitor_child_pids(parent_pid):
    """
    Continuously monitor and add child PIDs of a parent process to target_pids.
    Runs in a background thread.
    """
    print(f"Started monitoring child processes for parent PID: {parent_pid}")
    while True:
        try:
            # Get current child PIDs using pgrep
            output = subprocess.check_output(f"pgrep -P {parent_pid}", shell=True, text=True)
            child_pids = output.strip().split()

            # Update target_pids set dynamically
            with target_pids_lock:
                for pid in map(int, child_pids):
                    if pid not in target_pids:
                        print(f"Detected new child process: PID {pid}")
                        target_pids.add(pid)
        except subprocess.CalledProcessError:
            # No child processes currently found
            pass
        time.sleep(0.5)  # Monitor interval: 500ms


def run_web_gui():
    """
    Launch the web GUI using 'npm run dev' and keep it running.
    """
    try:
        frontend_dir = "./frontend" 
        print("Starting web GUI with 'npm run dev'...")

        # Allow some time for the server to start
        time.sleep(0.5)
        server = tracker.server
        if hasattr(server, "_server"):
            port = server._server.sockets[0].getsockname()[1]
            print(f"WebSocket server is running on port: {port}")
        else:
            print("Server has not started yet.")

        # Add the WebSocket port to the environment variables
        env = os.environ.copy()
        env["REACT_APP_PORT"] = str(port)

        # Start 'npm run dev' as a background process
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,
            env=env,
        )

        print(f"Web GUI started with PID: {process.pid}")

        # Monitor Vite output to find the actual port
        vite_port = None
        while True:
            line = process.stdout.readline()
            if not line:
                break

            print(f"[Web GUI]: {line.strip()}")

            # Match the port Vite is running on
            match = re.search(r"Local:\s+http://localhost:(\d+)", line)
            if match:
                vite_port = match.group(1)
                print(f"Vite development server is running on port {vite_port}")
                break

        if vite_port:
            print(f"Open your browser at: http://localhost:{vite_port}?port={port}")
        else:
            print("Failed to detect Vite server port.")

        # Wait for the process to finish
        process.wait()

    except KeyboardInterrupt:
        print("Shutting down web GUI...")
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except Exception as e:
        print(f"Error: {e}")
        if process:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)


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
command = sys.argv[1:]
if command[0] == "all":
    print("Tracing events for ALL processes...")
    trace_all = True
else:
    print(f"Running command: {' '.join(command)}")
    parent_pid = runner.run_command(command)
    with target_pids_lock:
        target_pids.add(parent_pid)

    # Start background monitoring for child PIDs
    monitor_thread = threading.Thread(target=monitor_child_pids, args=(parent_pid,), daemon=True)
    monitor_thread.start()
    print(f"Tracing PIDs (live): {target_pids}")


bpf_mmap["mmap_enter_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_enter_event(cpu, raw_data, size, tracker, target_pids.copy(), trace_all)
)
bpf_mmap["mmap_exit_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_exit_event(cpu, raw_data, size, tracker, target_pids.copy(), trace_all)
)
bpf_munmap["munmap_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_munmap(cpu, raw_data, size, tracker, target_pids.copy(), trace_all)
)
bpf_mremap["mremap_enter_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_mremap_enter(cpu, raw_data, size, tracker, target_pids.copy(), trace_all)
)
bpf_mremap["mremap_exit_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_mremap_exit(cpu, raw_data, size, tracker, target_pids.copy(), trace_all)
)
bpf_brk["brk_enter_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_brk_enter_event(cpu, raw_data, size, tracker, target_pids.copy(), trace_all)
)
bpf_brk["brk_exit_events"].open_perf_buffer(
    lambda cpu, raw_data, size: handle_brk_exit_event(cpu, raw_data, size, tracker, target_pids.copy(), trace_all)
)

# Start the usage thread
print(f"Starting usage thread with sleep interval of {USAGE_INTERVAL} seconds")
usage_thread = threading.Thread(target=fetch_usage_loop, args=[tracker, target_pids_lock, target_pids], daemon=True)
usage_thread.start()
print("Started usage thread")

print("Tracing and reporting events... Ctrl-C to stop.")

# Start the web GUI
web_gui_thread = threading.Thread(target=run_web_gui, daemon=True)
web_gui_thread.start()

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
