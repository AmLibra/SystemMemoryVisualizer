#include <linux/bpf.h>
#include <uapi/linux/ptrace.h>

// Define data structure for munmap events
struct munmap_data_t {
    u64 pid;            // Process ID
    u64 start_addr;     // Starting address of the memory region to be unmapped
    u64 size;           // Size of the memory region
    char comm[16];      // Process name
};

// Output buffer for munmap events
BPF_PERF_OUTPUT(munmap_events);

// Attach to sys_enter_munmap
int trace_munmap(struct tracepoint__syscalls__sys_enter_munmap *ctx) {
    struct munmap_data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.start_addr = ctx->addr;
    data.size = ctx->len;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    // Submit the munmap event
    munmap_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
