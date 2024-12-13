import threading
from collections import defaultdict
import math
import time
from utils.server import Server

SUMMARY_INTERVAL = 1  # seconds

class MemoryTracker:
    def __init__(self, page_size):
        self.page_size = page_size
        self.mmap_event_cache_lock = threading.Lock()
        self.mmap_event_cache = defaultdict(list)
        self.mremap_event_cache_lock = threading.Lock()
        self.mremap_event_cache = defaultdict(list)
        self.allocations = defaultdict(list)
        self.program_breaks = defaultdict(lambda: 0)  # Current program break per PID
        self.lock = threading.Lock()  # Lock for thread safety
        
        self.start_time = time.time_ns()
        
        self.server = Server()
        self.server.start_on_separate_thread()

    def add_allocation(self, pid, start_addr, size, comm):
        with self.lock:  # Ensure thread-safe access
            self._add_allocation(pid, start_addr, size, comm)

    def _add_allocation(self, pid, start_addr, size, comm):
        end_addr = start_addr + size
        num_pages = math.ceil(size / self.page_size)
        allocation = {
            "start_addr": start_addr,
            "end_addr": end_addr,
            "size": size,
            "pages": num_pages,
            "comm": comm,
        }
        allocations = self.allocations[pid]
        # Find the right position to insert while maintaining sorted order
        inserted = False
        for i, existing in enumerate(allocations):
            # If the new allocation overlaps with an existing one, skip adding it
            if not (end_addr <= existing["start_addr"] or start_addr >= existing["end_addr"]):
                return

            # Insert if it should come before the current entry
            if end_addr <= existing["start_addr"]:
                allocations.insert(i, allocation)
                inserted = True
                break

        # If not inserted, it should go at the end
        if not inserted:
            allocations.append(allocation)

        # Merge adjacent or overlapping allocations to coalesce memory ranges
        self._merge_allocations(pid)
        self._broadcast_allocations()

    def _merge_allocations(self, pid):
        """Merge adjacent or overlapping allocations for a process."""
        allocations = self.allocations[pid]
        merged = []

        for alloc in sorted(allocations, key=lambda x: x["start_addr"]):
            if not merged or merged[-1]["end_addr"] < alloc["start_addr"]:
                # No overlap, add to merged list
                merged.append(alloc)
            else:
                # Overlap or adjacent, merge with the last entry
                merged[-1]["end_addr"] = max(merged[-1]["end_addr"], alloc["end_addr"])
                merged[-1]["size"] = merged[-1]["end_addr"] - merged[-1]["start_addr"]
                merged[-1]["pages"] = math.ceil(merged[-1]["size"] / self.page_size)

        self.allocations[pid] = merged

    def remove_allocation(self, pid, start_addr, size):
        with self.lock:  # Ensure thread-safe access
            self._remove_allocation(pid, start_addr, size)

    def _remove_allocation(self, pid, start_addr, size):
        """Handle partial and complete unmap requests."""
        if pid not in self.allocations:
            print(f"[WARN] PID {pid}: No allocations found for unmap request "
                f"Start Address: {hex(start_addr)} | Size: {size}")
            return

        allocations = self.allocations[pid]
        new_allocations = []
        unmap_end_addr = start_addr + size
        unmapped = False

        for alloc in allocations:
            # No overlap, keep the allocation as-is
            if alloc["end_addr"] <= start_addr or alloc["start_addr"] >= unmap_end_addr:
                new_allocations.append(alloc)
                continue

            # Partial overlap: split the allocation
            if alloc["start_addr"] < start_addr and alloc["end_addr"] > unmap_end_addr:
                # Split into two parts
                new_allocations.append({
                    "start_addr": alloc["start_addr"],
                    "end_addr": start_addr,
                    "size": start_addr - alloc["start_addr"],
                    "pages": math.ceil((start_addr - alloc["start_addr"]) / self.page_size),
                    "comm": alloc["comm"],
                })
                new_allocations.append({
                    "start_addr": unmap_end_addr,
                    "end_addr": alloc["end_addr"],
                    "size": alloc["end_addr"] - unmap_end_addr,
                    "pages": math.ceil((alloc["end_addr"] - unmap_end_addr) / self.page_size),
                    "comm": alloc["comm"],
                })
                unmapped = True

            # Start of allocation overlaps
            elif alloc["start_addr"] < start_addr < alloc["end_addr"]:
                new_allocations.append({
                    "start_addr": alloc["start_addr"],
                    "end_addr": start_addr,
                    "size": start_addr - alloc["start_addr"],
                    "pages": math.ceil((start_addr - alloc["start_addr"]) / self.page_size),
                    "comm": alloc["comm"],
                })
                unmapped = True

            # End of allocation overlaps
            elif alloc["start_addr"] < unmap_end_addr < alloc["end_addr"]:
                new_allocations.append({
                    "start_addr": unmap_end_addr,
                    "end_addr": alloc["end_addr"],
                    "size": alloc["end_addr"] - unmap_end_addr,
                    "pages": math.ceil((alloc["end_addr"] - unmap_end_addr) / self.page_size),
                    "comm": alloc["comm"],
                })
                unmapped = True

            # Fully overlaps, remove the allocation
            else:
                unmapped = True

        if not unmapped:
            print(f"[WARN] PID {pid}: Unmap request doesn't match any tracked allocation "
                f"Start Address: {hex(start_addr)} | Size: {size}")

        self.allocations[pid] = new_allocations
        self._broadcast_allocations()

    def _broadcast_allocations(self):
        self.server.notify_clients_threadsafe({
            "type": "allocations",
            "time": time.time_ns() - self.start_time,
            "allocations": list(map(
                lambda x: {
                    "pid": x[0],
                    "allocations": list(map(
                        lambda a: {
                            "startAddr": math.ceil(a["start_addr"] / self.page_size),
                            "endAddr": math.ceil(a["end_addr"] / self.page_size),
                            "size": a["size"],
                            "pages": a["pages"],
                            "comm": a["comm"],
                        },
                        x[1]
                    ))
                },
                self.allocations.items()
            )),
        })
        pass

    def handle_brk(self, pid, tid, new_brk, comm):
        """Handle a brk syscall and update the program break."""
        key = (pid, tid)  # Unique key for process and thread
        with self.lock:  # Ensure thread-safe access
            old_brk = self.program_breaks.get(key, 0)

            # If no previous `brk` observed for this TID, initialize
            if old_brk == 0:
                self.program_breaks[key] = new_brk
                print(f"[INFO] Initialized heap tracking for PID {pid}, TID {tid} with base {hex(new_brk)}")
                return

            # Update the program break
            self.program_breaks[key] = new_brk

            # Adjust allocations based on the change in the program break
            if new_brk > old_brk:
                # Memory region expanded
                self._add_allocation(pid, old_brk, new_brk - old_brk, comm)
            elif new_brk < old_brk:
                # Memory region shrunk
                self._remove_allocation(pid, new_brk, old_brk - new_brk)

    def summarize_allocations_loop(self):
        while True:
            self.summarize_allocations()
            time.sleep(SUMMARY_INTERVAL)  

    def summarize_allocations(self):
        self.server.notify_clients_threadsafe({
            "type": "time",
            "time": time.time_ns() - self.start_time,
        }, save_event=False)

        with self.lock:  # Ensure thread-safe read access
            print("\n[Summary of Virtual Memory allocations]")
            for pid, allocations in self.allocations.items():
                total_size = sum(a["size"] for a in allocations)
                total_pages = sum(a["pages"] for a in allocations)
                print(f"PID: {pid} | Total Allocations: {len(allocations)} | Total Size (B): {total_size:<10} | Total Pages: {total_pages:<5}")
                for alloc in allocations:
                    print(f"    Address Range: {hex(alloc['start_addr']):} - {hex(alloc['end_addr']):<30} | "
                        f"Size (B): {alloc['size']:<10} | Pages: {alloc['pages']:<10} | Command: {alloc['comm']}")
            print("\n---")
            print("Number of observed Processes: ", len(set(self.allocations.keys())))
            size = sum(sum(a["size"] for a in allocations) for allocations in self.allocations.values())
            formatted_size = "{:.2f}".format(size / 1024 / 1024)
            print("Number of observed Allocations: ", sum(len(allocations) for allocations in self.allocations.values()))
            print("Total Allocated Virtual Memory: ", formatted_size, "MB")
            formatted_pg_size = "{}".format(int(self.page_size / 1024))
            print("Total Allocated Pages (" + formatted_pg_size + " KB): ", sum(sum(a["pages"] for a in allocations) for allocations in self.allocations.values()))
