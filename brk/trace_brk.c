#include <linux/bpf.h>
#include <uapi/linux/ptrace.h>

struct brk_data_t {
    u64 pid;          // Process ID
    u64 requested_brk; // Requested new program break
    char comm[16];    // Process name
    u64 tid;          // Thread ID
};

struct brk_exit_data_t {
    u64 pid;          // Process ID
    u64 actual_brk;    // Actual program break after the call
    char comm[16];    // Process name
    u64 tid;          // Thread ID
};

BPF_PERF_OUTPUT(brk_enter_events);
BPF_PERF_OUTPUT(brk_exit_events);

int trace_brk_enter(struct tracepoint__syscalls__sys_enter_brk *ctx) {
    struct brk_data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.requested_brk = ctx->brk;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    data.tid = bpf_get_current_pid_tgid() & 0xFFFFFFFF; // Thread ID

    brk_enter_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

int trace_brk_exit(struct tracepoint__syscalls__sys_exit_brk *ctx) {
    struct brk_exit_data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.actual_brk = ctx->ret; // The return value of brk()
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    data.tid = bpf_get_current_pid_tgid() & 0xFFFFFFFF; // Thread ID

    brk_exit_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
