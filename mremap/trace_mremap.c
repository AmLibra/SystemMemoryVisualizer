#include <linux/bpf.h>
#include <uapi/linux/ptrace.h>

struct mremap_data_t {
    u64 pid;
    u64 old_addr;  // Original address of the memory region
    u64 old_size;  // Original size of the memory region
    u64 new_addr;  // New address of the memory region
    u64 new_size;  // New size of the memory region
    char comm[16]; // Process name
};

struct mremap_exit_data_t {
    u64 pid;
    u64 new_addr;  // New address of the memory region
};

BPF_PERF_OUTPUT(mremap_enter_events);
BPF_PERF_OUTPUT(mremap_exit_events);

int trace_mremap_enter(struct tracepoint__syscalls__sys_enter_mremap *ctx) {
    struct mremap_data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.old_addr = ctx->addr;
    data.old_size = ctx->old_len;
    data.new_size = ctx->new_len;
    data.new_addr = ctx->new_addr;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    mremap_enter_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

int trace_mremap_exit(struct tracepoint__syscalls__sys_exit_mremap *ctx) {
    struct mremap_exit_data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.new_addr = ctx->ret; // New address returned by mremap

    mremap_exit_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
