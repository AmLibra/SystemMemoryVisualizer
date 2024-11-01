from bcc import BPF
import time
import sys

# Configuration for many probes
PROBES = [
    {
        "file": "mmap/trace_mmap.c",                # Path to the BPF program that receives the probe events
        "probe_type": "tracepoint",                 # tracepoints seem to be more reliable for portability between kernel versions
        "probe_name": "syscalls:sys_enter_mmap",    # The tracepoint name ('sudo bpftrace -l' for a list)
        "function_name": "trace_mmap",              # The function in the BPF program to call
        "event_key": "mmap_events"                  # The key to access the event in the BPF instance (same as in the BPF program)
    },
    # Add additional probes here as needed as per the mmap example
]

POLL_TIMEOUT = 1 # Poll timeout in milliseconds, to allow for responsive Ctrl-C

# Ensure PIDs are provided as arguments
if len(sys.argv) < 2:
    print("Usage: sudo python3 run_kprobes.py <PID>")
    sys.exit(1)

# Support all PIDs if "all" is provided
all = "all" in sys.argv
if not all: # Get the PIDs 
    test_pids = [int(pid) for pid in sys.argv[1:]]


# Load and attach each probe
bpf_programs = []
for probe in PROBES:
    bpf_code = open(probe["file"]).read()
    b = BPF(text=bpf_code)
    if probe["probe_type"] == "kprobe":
        b.attach_kprobe(event=probe["probe_name"], fn_name=probe["function_name"])
    elif probe["probe_type"] == "tracepoint":
        b.attach_tracepoint(tp=probe["probe_name"], fn_name=probe["function_name"])
    # Store the BPF instance with event key for access
    bpf_programs.append({"bpf": b, "event_key": probe["event_key"]})
    print(f"Attached {probe['probe_type']} {probe['probe_name']}")

print("Tracing events... Ctrl-C to end.")

# Define a generic callback function for event printing
def print_event(cpu, data, size, event_key, bpf_instance):
    event = bpf_instance[event_key].event(data)
    if all or event.pid in test_pids:
        print(f"Process: {event.comm.decode('utf-8', 'replace')} | PID: {event.pid} | Address: {hex(event.address)} | Size: {event.size}")

# Open perf buffers and set up callbacks for each probe
for program in bpf_programs:
    bpf_instance = program["bpf"]
    event_key = program["event_key"]
    bpf_instance[event_key].open_perf_buffer(lambda cpu, data, size, event_key=event_key, bpf_instance=bpf_instance:
                                             print_event(cpu, data, size, event_key, bpf_instance))

# Poll all perf buffers in a single loop
try:
    while True:
        for program in bpf_programs:
            program["bpf"].perf_buffer_poll(timeout=int(POLL_TIMEOUT))
except KeyboardInterrupt:
    print("Detaching...")
    for program in bpf_programs:
        program["bpf"].cleanup()
    sys.exit(0)
