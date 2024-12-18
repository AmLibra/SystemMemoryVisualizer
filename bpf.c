#include <linux/bpf.h>
#include <linux/ptrace.h>


// ==== map declarations ================================================================

BPF_RINGBUF_OUTPUT(events, 1024);

// ======================================================================================


// ==== brk =============================================================================

struct brk_data_t {
    u64 type;
    u64 pid_and_tid;          // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 requested_brk; // Requested new program break
    char comm[16];    // Process name
};

struct brk_exit_data_t {
    u64 type;
    u64 pid_and_tid;          // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 actual_brk;    // Actual program break after the call
    char comm[16];    // Process name
};

int trace_brk_enter(struct tracepoint__syscalls__sys_enter_brk *ctx) {
    struct brk_data_t data = {};
    data.type = 6;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.requested_brk = ctx->brk;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));


    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

int trace_brk_exit(struct tracepoint__syscalls__sys_exit_brk *ctx) {
    struct brk_exit_data_t data = {};
    data.type = 7;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.actual_brk = ctx->ret; // The return value of brk()
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

// ======================================================================================


// ==== mmap ============================================================================

// Structure for sys_enter_mmap events
struct mmap_data_t {
    u64 type;
    u64 pid_and_tid;            // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 requested_addr;         // Address passed to mmap (could be 0)
    u64 size;                   // Requested memory size
    char comm[16];              // Process name
};

// Structure for sys_exit_mmap events
struct mmap_exit_data_t {
    u64 type;
    u64 pid_and_tid;          // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 actual_addr;    // Address returned by mmap
};

int trace_mmap_enter(struct tracepoint__syscalls__sys_enter_mmap *ctx) {
    struct mmap_data_t data = {};
    data.type = 1;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.requested_addr = ctx->addr;
    data.size = ctx->len;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

int trace_mmap_exit(struct tracepoint__syscalls__sys_exit_mmap *ctx) {
    struct mmap_exit_data_t data = {};
    data.type = 2;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.actual_addr = ctx->ret;

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

// ======================================================================================


// ==== mremap ==========================================================================

struct mremap_data_t {
    u64 type;
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 old_addr;               // Original address of the memory region
    u64 old_size;               // Original size of the memory region
    u64 new_addr;               // New address of the memory region
    u64 new_size;               // New size of the memory region
    u64 flags;                  // flags
    char comm[16];              // Process name
};

struct mremap_exit_data_t {
    u64 type;
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 new_addr;               // New address of the memory region
};

int trace_mremap_enter(struct tracepoint__syscalls__sys_enter_mremap *ctx) {
    struct mremap_data_t data = {};
    data.type = 3;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.old_addr = ctx->addr;
    data.old_size = ctx->old_len;
    data.new_size = ctx->new_len;
    data.new_addr = ctx->new_addr;
    data.flags = ctx->flags;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

int trace_mremap_exit(struct tracepoint__syscalls__sys_exit_mremap *ctx) {
    struct mremap_exit_data_t data = {};
    data.type = 4;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.new_addr = ctx->ret; // New address returned by mremap

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

// ======================================================================================


// ==== munmap ==========================================================================

// Define data structure for munmap events
struct munmap_data_t {
    u64 type;
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 start_addr;             // Starting address of the memory region to be unmapped
    u64 size;                   // Size of the memory region
    char comm[16];              // Process name
};

// Attach to sys_enter_munmap
int trace_munmap(struct tracepoint__syscalls__sys_enter_munmap *ctx) {
    struct munmap_data_t data = {};
    data.type = 5;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.start_addr = ctx->addr;
    data.size = ctx->len;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    // Submit the munmap event
    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

// ======================================================================================


// ==== clone ===========================================================================

// Structures for clone events
struct clone_enter_data_t {
    u64 type;
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 flags;
    char comm[16];
};

struct clone_exit_data_t {
    u64 type;
    u64 pid_and_tid;
    u64 timestamp;

    u64 child_pid;
};

int trace_clone_enter(struct tracepoint__syscalls__sys_enter_clone *ctx) {
    struct clone_enter_data_t data = {};
    data.type = 8;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.flags = ctx->clone_flags;

    if ((data.flags & 0x00010000) == 0x00010000) {
        // skip, the thread is being created, not the process
        return 0;
    }

    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

int trace_clone_exit(struct tracepoint__syscalls__sys_exit_clone *ctx) {
    struct clone_exit_data_t data = {};
    data.type = 9;
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.child_pid = ctx->ret;

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}


// ==== clone3 ==========================================================================

struct clone3_enter_data_t {
    u64 type;
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 timestamp;

    u64 flags;
    u64 pidfd;                 // PID file descriptor
    u64 child_tid;             // Child TID
    u64 parent_tid;            // Parent TID
    char comm[16];
};

struct clone3_exit_data_t {
    u64 type;
    u64 pid_and_tid;
    u64 timestamp;

    u64 child_pid;
};

int trace_clone3_enter(struct tracepoint__syscalls__sys_enter_clone3 *ctx) {
    struct clone3_enter_data_t data = {};
    struct clone_args args = {};
    
    data.type = 10; 
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    bpf_probe_read_user(&args, sizeof(args), ctx->uargs);

    data.flags = args.flags;
    data.pidfd = args.pidfd;
    data.child_tid = args.child_tid;
    data.parent_tid = args.parent_tid;

    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

int trace_clone3_exit(struct tracepoint__syscalls__sys_exit_clone3 *ctx) {
    struct clone3_exit_data_t data = {};
    data.type = 11; 
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.child_pid = ctx->ret;

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

// ======================================================================================


// ==== vfork ===========================================================================

struct vfork_enter_data_t {
    u64 type;
    u64 pid_and_tid;           // Process ID << 32 | Thread ID
    u64 timestamp;

    char comm[16];
};

struct vfork_exit_data_t {
    u64 type;
    u64 pid_and_tid;
    u64 timestamp;

    u64 child_pid;
};

int trace_vfork_enter(struct tracepoint__syscalls__sys_enter_vfork *ctx) {
    struct vfork_enter_data_t data = {};
    data.type = 12; 
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

int trace_vfork_exit(struct tracepoint__syscalls__sys_exit_vfork *ctx) {
    struct vfork_exit_data_t data = {};
    data.type = 13; 
    data.pid_and_tid = bpf_get_current_pid_tgid();
    data.timestamp = bpf_ktime_get_ns();

    data.child_pid = ctx->ret;

    events.ringbuf_output(&data, sizeof(data), 0);
    return 0;
}

// ======================================================================================

