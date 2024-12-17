#include <linux/bpf.h>
#include <linux/ptrace.h>


// ==== map declarations ================================================================

BPF_PERF_OUTPUT(brk_events);
BPF_PERF_OUTPUT(mmap_events);
BPF_PERF_OUTPUT(mremap_events);
BPF_PERF_OUTPUT(munmap_events);
BPF_PERF_OUTPUT(clone_events);

// ======================================================================================


// ==== brk =============================================================================

struct brk_data_t {
    u64 pid_and_tid;          // Process ID << 32 | Thread ID
    u64 requested_brk; // Requested new program break
    char comm[16];    // Process name
};

struct brk_exit_data_t {
    u64 pid_and_tid;          // Process ID << 32 | Thread ID
    u64 actual_brk;    // Actual program break after the call
    char comm[16];    // Process name
    char dummy;         // field that would make the size of the event different than brk_data_t
};

int trace_brk_enter(struct tracepoint__syscalls__sys_enter_brk *ctx) {
    struct brk_data_t data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.requested_brk = ctx->brk;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));


    brk_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

int trace_brk_exit(struct tracepoint__syscalls__sys_exit_brk *ctx) {
    struct brk_exit_data_t data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.actual_brk = ctx->ret; // The return value of brk()
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    brk_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

// ======================================================================================


// ==== mmap ============================================================================

// Structure for sys_enter_mmap events
struct mmap_data_t {
    u64 pid_and_tid;          // Process ID << 32 | Thread ID
    u64 requested_addr; // Address passed to mmap (could be 0)
    u64 size;           // Requested memory size
    char comm[16];      // Process name
};

// Structure for sys_exit_mmap events
struct mmap_exit_data_t {
    u64 pid_and_tid;          // Process ID << 32 | Thread ID
    u64 actual_addr;    // Address returned by mmap
};

int trace_mmap_enter(struct tracepoint__syscalls__sys_enter_mmap *ctx) {
    struct mmap_data_t data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.requested_addr = ctx->addr;
    data.size = ctx->len;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    mmap_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

int trace_mmap_exit(struct tracepoint__syscalls__sys_exit_mmap *ctx) {
    struct mmap_exit_data_t exit_data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    exit_data.actual_addr = ctx->ret;

    mmap_events.perf_submit(ctx, &exit_data, sizeof(exit_data));
    return 0;
}

// ======================================================================================


// ==== mremap ==========================================================================

struct mremap_data_t {
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 old_addr;               // Original address of the memory region
    u64 old_size;               // Original size of the memory region
    u64 new_addr;               // New address of the memory region
    u64 new_size;               // New size of the memory region
    char comm[16];              // Process name
};

struct mremap_exit_data_t {
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 new_addr;               // New address of the memory region
};

int trace_mremap_enter(struct tracepoint__syscalls__sys_enter_mremap *ctx) {
    struct mremap_data_t data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.old_addr = ctx->addr;
    data.old_size = ctx->old_len;
    data.new_size = ctx->new_len;
    data.new_addr = ctx->new_addr;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    mremap_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

int trace_mremap_exit(struct tracepoint__syscalls__sys_exit_mremap *ctx) {
    struct mremap_exit_data_t data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.new_addr = ctx->ret; // New address returned by mremap

    mremap_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

// ======================================================================================


// ==== munmap ==========================================================================

// Define data structure for munmap events
struct munmap_data_t {
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 start_addr;             // Starting address of the memory region to be unmapped
    u64 size;                   // Size of the memory region
    char comm[16];              // Process name
};

// Attach to sys_enter_munmap
int trace_munmap(struct tracepoint__syscalls__sys_enter_munmap *ctx) {
    struct munmap_data_t data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.start_addr = ctx->addr;
    data.size = ctx->len;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    // Submit the munmap event
    munmap_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

// ======================================================================================


// ==== clone ===========================================================================

// Structures for clone events
struct clone_enter_data_t {
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 flags;
    u64 newsp;
    u64 parent_tid;
    u64 child_tid;
    u64 tls;
    char comm[16];
};

struct clone_exit_data_t {
    u64 pid_and_tid;
    u64 child_pid;
    c_char dummy;
};

int trace_clone_enter(struct tracepoint__syscalls__sys_enter_clone *ctx) {
    struct clone_enter_data_t data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.flags = ctx->args[0];
    data.newsp = ctx->args[1];
    data.parent_tid = ctx->args[2];
    data.child_tid = ctx->args[3];
    data.tls = ctx->args[4];
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    clone_events.perf_submit(ctx, &data, sizeof(data));
    mmap_events.perf_submit(ctx, &data, sizeof(data));
    mremap_events.perf_submit(ctx, &data, sizeof(data));
    munmap_events.perf_submit(ctx, &data, sizeof(data));
    brk_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

int trace_clone_exit(struct tracepoint__syscalls__sys_exit_clone *ctx) {
    struct clone_exit_data_t data = {};
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.child_pid = ctx->ret;

    clone_events.perf_submit(ctx, &data, sizeof(data));
    mmap_events.perf_submit(ctx, &data, sizeof(data));
    mremap_events.perf_submit(ctx, &data, sizeof(data));
    munmap_events.perf_submit(ctx, &data, sizeof(data));
    brk_events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

// ======================================================================================

