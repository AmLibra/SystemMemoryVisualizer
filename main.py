#!/usr/bin/python3

from bcc import BPF
from tracers.event_cache import EventCache
from tracers.events import handle_event, set_tracker_pid
from utils.tracker import MemoryTracker
from usage.usage import USAGE_INTERVAL, fetch_usage_loop
from utils.runner import Runner
from tracers.common import PAGE_SIZE
import threading
import time
import subprocess
import os
import re


# Initialize Runner
runner = Runner()
# Initialize MemoryTracker
tracker = MemoryTracker(PAGE_SIZE)
# Create event cache
event_cache = EventCache()
# Create tracked PID set
tracked_pids_lock = threading.Lock()
tracked_pids = set()


import threading, sys, traceback

def dumpstacks(signal, frame):
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId,""), threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    print("\n".join(code))

import signal
signal.signal(signal.SIGUSR1, dumpstacks)

def kill_processes_by_name(name):
    try:
        result = subprocess.run(["pgrep", "-f", name], stdout=subprocess.PIPE, text=True)
        pids = result.stdout.splitlines()

        for pid in pids:
            print(f"Killing process {pid} ({name})")
            os.kill(int(pid), signal.SIGKILL)

    except Exception as e:
        print(f"Error killing processes: {e}")

def run_web_gui():
    """
    Launch the web GUI using 'npm run dev' and keep it running.
    """
    try:
        frontend_dir = os.path.dirname(os.path.realpath(__file__)) + "/frontend"
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


# Start the usage thread
print(f"Starting usage thread with sleep interval of {USAGE_INTERVAL} seconds")
usage_thread = threading.Thread(target=fetch_usage_loop, args=[tracker, tracked_pids_lock, tracked_pids], daemon=True)
usage_thread.start()
print("Started usage thread")

print("Tracing and reporting events... Ctrl-C to stop.")

# Start the web GUI
web_gui_thread = threading.Thread(target=run_web_gui, daemon=True)
web_gui_thread.start()


print("Initializing BPF programs...")

bpf_file = BPF(src_file="bpf.c")
print("\t Loaded BPF program successfully")

# Attach tracepoints
print("Attaching tracepoints...")
bpf_file.attach_tracepoint(tp="syscalls:sys_enter_mmap", fn_name="trace_mmap_enter")
print("\t Attached to sys_enter_mmap")
bpf_file.attach_tracepoint(tp="syscalls:sys_exit_mmap", fn_name="trace_mmap_exit")
print("\t Attached to sys_exit_mmap")
bpf_file.attach_tracepoint(tp="syscalls:sys_enter_munmap", fn_name="trace_munmap")
print("\t Attached to sys_enter_munmap")
bpf_file.attach_tracepoint(tp="syscalls:sys_enter_mremap", fn_name="trace_mremap_enter")
print("\t Attached to sys_enter_mremap")
bpf_file.attach_tracepoint(tp="syscalls:sys_exit_mremap", fn_name="trace_mremap_exit")
print("\t Attached to sys_exit_mremap")
bpf_file.attach_tracepoint(tp="syscalls:sys_enter_brk", fn_name="trace_brk_enter")
print("\t Attached to sys_enter_brk")
bpf_file.attach_tracepoint(tp="syscalls:sys_exit_brk", fn_name="trace_brk_exit")
print("\t Attached to sys_exit_brk")
bpf_file.attach_tracepoint(tp="syscalls:sys_enter_clone", fn_name="trace_clone_enter")
print("\t Attached to sys_enter_clone")
bpf_file.attach_tracepoint(tp="syscalls:sys_exit_clone", fn_name="trace_clone_exit")
print("\t Attached to sys_exit_clone")
bpf_file.attach_tracepoint(tp="syscalls:sys_enter_clone3", fn_name="trace_clone3_enter")
print("\t Attached to sys_enter_clone3")
bpf_file.attach_tracepoint(tp="syscalls:sys_exit_clone3", fn_name="trace_clone3_exit")
print("\t Attached to sys_exit_clone3")

def attach_tracepoint_if_exists(bpf, tp, fn_name):
    try:
        bpf.attach_tracepoint(tp=tp, fn_name=fn_name)
        print(f"\t Attached to {tp}")
    except Exception as e:
        print(f"\t Ignoring tracepoint {tp}: {e}")

attach_tracepoint_if_exists(bpf_file, "syscalls:sys_enter_vfork", "trace_vfork_enter")
attach_tracepoint_if_exists(bpf_file, "syscalls:sys_exit_vfork", "trace_vfork_exit")

pid = os.getpid()
set_tracker_pid(pid)
print("Tracker PID set to", pid)

bpf_file["events"].open_ring_buffer(
    lambda cpu, raw_data, size: handle_event(cpu, raw_data, size, tracker, tracked_pids, event_cache)
)

command = sys.argv[1:]
parent_pid = runner.run_command(command)

# Handle exit and cleanup
try:
    while True:
        bpf_file.ring_buffer_poll()
except KeyboardInterrupt:
    print("Exiting...")
finally:
    runner.cleanup()
