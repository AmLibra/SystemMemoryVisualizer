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

# Function to randomly resize mapped memory
def random_mremap(file_name, size):
    with open(file_name, "r+b") as f:
        # Map the entire file into memory
        with mmap.mmap(f.fileno(), size) as mmapped_file:
            # Perform random resizing (simulates mremap)
            new_size = random.choice([size, size * 2, size // 2])  # Double, half, or same size
            try:
                mmapped_file.resize(new_size)  # Resize the memory region
                print(f"Resized mmap: {file_name}, Old Size: {size}, New Size: {new_size}")
            except ValueError as e:
                print(f"Failed to resize mmap: {e}")

# Continuously map, resize, and unmap memory with varied patterns
for _ in range(100):
    # Choose a random file and access pattern
    file_name = random.choice(file_names)
    size = os.path.getsize(file_name)
    random_mremap(file_name, size)
    time.sleep(1)  # Delay to keep each mmap active for a short time

# Clean up by removing the test files
for file_name in file_names:
    os.remove(file_name)
