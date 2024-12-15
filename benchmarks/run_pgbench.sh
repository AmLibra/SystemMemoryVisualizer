#!/bin/bash

# Script to Run PostgreSQL Benchmark via main.py
set -e

echo "========== Running PostgreSQL Benchmark =========="

# Benchmark Parameters
DB_NAME="pgbench_test"
CLIENTS=10000     # Number of concurrent clients
THREADS=200     # Number of worker threads
DURATION=60   # Benchmark duration in seconds
SCALE=1000     # Scale factor for ~50 million rows

# Activate Python Virtual Environment
echo "Activating Python virtual environment..."
source .venv/bin/activate

# Set PYTHONPATH for BCC (if required)
export PYTHONPATH=$(dirname $(find /usr/lib -name bcc)):$PYTHONPATH

# Command to run PostgreSQL Benchmark
PG_BENCH_CMD="sudo -u postgres pgbench -c $CLIENTS -j $THREADS -T $DURATION $DB_NAME -s $SCALE" 

# Run Python Script and Pass Command as Argument
echo "Passing pgbench command to main.py..."
python3 ./main.py $PG_BENCH_CMD

echo "========== Benchmark Execution Complete =========="
