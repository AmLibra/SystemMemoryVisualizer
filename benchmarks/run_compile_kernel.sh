#!/bin/bash

# Linux Kernel Compilation Benchmark Script
set -e

echo "========== Running Linux Kernel Compilation Benchmark =========="

# Kernel Version and Directories
KERNEL_VERSION="6.6.1"
KERNEL_DIR="benchmarks/linux-$KERNEL_VERSION"

# Activate Python Virtual Environment
echo "Activating Python virtual environment..."
source .venv/bin/activate

# Set PYTHONPATH for BCC (if required)
export PYTHONPATH=$(dirname $(find /usr/lib -name bcc)):$PYTHONPATH

# Command to Run Kernel Compilation
KERNEL_BUILD_CMD="make -C $KERNEL_DIR"

# Run Python Script and Pass Command as Argument
echo "Passing kernel compilation command to main.py..."
python3 ./main.py $KERNEL_BUILD_CMD

echo "========== Kernel Compilation Benchmark Execution Complete =========="
