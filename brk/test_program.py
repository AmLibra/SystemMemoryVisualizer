#!/usr/bin/env python3
import ctypes
import time
import random

# Load libc to access brk and sbrk
libc = ctypes.CDLL("libc.so.6", use_errno=True)

# Wrapper for brk
def brk(addr=None):
    if addr is None:
        return libc.brk(0)  # Get the current program break
    else:
        return libc.brk(addr)  # Set the program break to addr

# Wrapper for sbrk
def sbrk(increment):
    return libc.sbrk(increment)

# Function to randomly adjust the program break
def random_brk_operations():
    current_brk = brk()  # Get the current program break
    print(f"Initial program break: {hex(current_brk)}")

    for _ in range(100):  # Perform 100 operations
        operation = random.choice(["expand", "shrink", "reset"])
        if operation == "expand":
            increment = random.choice([4096, 8192, 16384])  # Random increments (4KB, 8KB, 16KB)
            result = sbrk(increment)
            if result != -1:
                print(f"[Expand] Increased program break by {increment} bytes. New break: {hex(result)}")
            else:
                print("[Expand] Failed to increase program break.")
        elif operation == "shrink":
            decrement = random.choice([4096, 8192])  # Random decrements (4KB, 8KB)
            result = sbrk(-decrement)
            if result != -1:
                print(f"[Shrink] Decreased program break by {decrement} bytes. New break: {hex(result)}")
            else:
                print("[Shrink] Failed to decrease program break.")
        elif operation == "reset":
            initial_brk = brk(0)  # Reset to initial
            if brk(initial_brk) == 0:
                print(f"[Reset] Reset program break to {hex(initial_brk)}")
            else:
                print("[Reset] Failed to reset program break.")

        time.sleep(1)  # Delay to simulate time between operations

    # Final program break
    final_brk = brk()
    print(f"Final program break: {hex(final_brk)}")

# Main function to execute the test
if __name__ == "__main__":
    print("Starting brk and sbrk test...")
    random_brk_operations()
    print("Test complete.")
