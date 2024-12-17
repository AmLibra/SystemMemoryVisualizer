#include <linux/bpf.h>
#include <uapi/linux/bpf.h>
#include <linux/ptrace.h>

// Structures for clone events
struct clone_enter_data_t {
    u64 pid;
    u64 flags;
    u64 newsp;
    u64 parent_tid;
    u64 child_tid;
    u64 tls;
    char comm[16];
};

struct clone_exit_data_t {
    u64 pid;
    u64 child_pid;
};

BPF_PERF_OUTPUT(clone_enter_events);
BPF_PERF_OUTPUT(clone_exit_events);

int trace_clone_enter(struct tracepoint__syscalls__sys_enter_clone *ctx) {
    struct clone_enter_data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.flags = ctx->args[0];
    data.newsp = ctx->args[1];
    data.parent_tid = ctx->args[2];
    data.child_tid = ctx->args[3];
    data.tls = ctx->args[4];
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    clone_enter_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

int trace_clone_exit(struct tracepoint__syscalls__sys_exit_clone *ctx) {
    struct clone_exit_data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.child_pid = ctx->ret;

    clone_exit_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
