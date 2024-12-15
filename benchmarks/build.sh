#!/bin/bash

# PostgreSQL Benchmark Setup Script
set -e

echo "========== Setting Up PostgreSQL Benchmark Tools =========="

# Install PostgreSQL and dependencies
echo "Installing PostgreSQL and pgbench..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create Benchmark Database
DB_NAME="pgbench_test"

echo "Setting up PostgreSQL database: $DB_NAME"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"

# Initialize pgbench data
SCALE=50  # Scale factor for ~50 million rows

echo "Initializing pgbench with scale factor $SCALE..."
sudo -u postgres pgbench -i -s $SCALE $DB_NAME

echo "========== PostgreSQL Benchmark Setup Complete =========="


# Linux Kernel Compilation Setup Script
echo "========== Setting Up Linux Kernel Compilation Benchmark =========="

# Install build dependencies
echo "Installing build tools and dependencies..."
sudo apt install -y build-essential libncurses-dev bison flex libssl-dev libelf-dev wget

# Download the latest stable Linux kernel
KERNEL_VERSION="6.6.1"  # Example version; adjust as needed
KERNEL_DIR="linux-$KERNEL_VERSION"

if [ ! -d "$KERNEL_DIR" ]; then
    echo "Downloading Linux kernel version $KERNEL_VERSION..."
    wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-$KERNEL_VERSION.tar.xz
    echo "Extracting kernel source..."
    tar -xf linux-$KERNEL_VERSION.tar.xz
    echo "Kernel source extracted successfully."
    rm linux-$KERNEL_VERSION.tar.xz
    echo "Kernel source cleaned up."
else
    echo "Linux kernel source already exists."
fi

echo "========== Linux Kernel Setup Complete =========="
