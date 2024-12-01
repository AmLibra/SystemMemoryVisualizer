#include <linux/bpf.h>
#include <uapi/linux/bpf.h>
#include <linux/ptrace.h>

// Structure for sys_enter_mmap events
struct mmap_data_t {
    u64 pid;
    u64 requested_addr; // Address passed to mmap (could be 0)
    u64 size;           // Requested memory size
    char comm[16];      // Process name
};

// Structure for sys_exit_mmap events
struct mmap_exit_data_t {
    u64 pid;
    u64 actual_addr;    // Address returned by mmap
};

BPF_PERF_OUTPUT(mmap_enter_events);
BPF_PERF_OUTPUT(mmap_exit_events);

int trace_mmap_enter(struct tracepoint__syscalls__sys_enter_mmap *ctx) {
    struct mmap_data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.requested_addr = ctx->addr;
    data.size = ctx->len;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    mmap_enter_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

int trace_mmap_exit(struct tracepoint__syscalls__sys_exit_mmap *ctx) {
    struct mmap_exit_data_t exit_data = {};
    exit_data.pid = bpf_get_current_pid_tgid() >> 32;
    exit_data.actual_addr = ctx->ret;

    mmap_exit_events.perf_submit(ctx, &exit_data, sizeof(exit_data));
    return 0;
}
