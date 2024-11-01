#include <uapi/linux/ptrace.h>
#include <linux/sched.h>
#include <linux/types.h>

struct mmap_data_t {
    u64 address;
    u64 size;
    u32 pid;
    char comm[16];  // Process name (16 bytes max for compatibility)
};

BPF_PERF_OUTPUT(mmap_events);  // Use perf buffer to send data to user space, I see it as a go channel

int trace_mmap(struct tracepoint__syscalls__sys_enter_mmap *ctx) {
    struct mmap_data_t data = {};

    // Fill the data structure with mmap parameters
    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.address = ctx->addr;
    data.size = ctx->len;

    // Retrieve the process name (command name)
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    // Submit the event
    mmap_events.perf_submit(ctx, &data, sizeof(data)); // mmap_events <- data
    return 0;
}
