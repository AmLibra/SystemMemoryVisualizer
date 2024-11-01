#!/usr/bin/env python3
import mmap
import os
import time
import random

# Create multiple files with varying sizes
file_sizes = [10 * 1024 * 1024, 5 * 1024 * 1024, 1 * 1024 * 1024]  # 10 MB, 5 MB, 1 MB
file_names = ["testfile1", "testfile2", "testfile3"]

# Initialize files with different sizes
for file_name, size in zip(file_names, file_sizes):
    with open(file_name, "wb") as f:
        f.write(b"\0" * size)

# Function to randomly access and modify mapped memory
def random_mmap_access(file_name, size):
    with open(file_name, "r+b") as f:
        # Map part or all of the file into memory
        mmap_size = random.choice([size, size // 2, 4096])  # Full, half, or 4 KB
        with mmap.mmap(f.fileno(), mmap_size) as mmapped_file:
            # Perform a random write within the mapped area
            offset = random.randint(0, mmap_size - 1)
            mmapped_file[offset] = random.randint(0, 255)
            # Read access to simulate different access patterns
            _ = mmapped_file[offset]

# Continuously map, access, and unmap memory with varied patterns
for _ in range(100):
    # Choose a random file and access pattern
    file_name = random.choice(file_names)
    size = os.path.getsize(file_name)
    random_mmap_access(file_name, size)
    time.sleep(0.1)  # Delay to keep each mmap active for a short time

# Clean up by removing the test files
for file_name in file_names:
    os.remove(file_name)
