# SystemMemoryVisualizer

This project includes scripts and tools that will be used to monitor and analyze the behavior of programs running on a Linux system. 
This documentation refers to the first module of the project, which is focused on the use of BPF to monitor system calls.
The scripts in this module are written in Python and use the BCC library to interact with the BPF programs.

## Installation
To install the necessary BPF tools and dependencies, run the following commands:

```bash
sudo apt update
sudo apt install -y bpfcc-tools linux-headers-$(uname -r) libbpfcc-dev libbpfcc libelf-dev python3-bpfcc
```

## Activating the Virtual Environment

This project uses a Python virtual environment for dependency management[^1].

[^1]: Instructions in this section are based on the [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/).

To create it, use the following command:

```bash
python3 -m venv .venv
```

You can then enable the virtual environment using:

```bash
source .venv/bin/activate
```

Then, install the project requirements with:

```bash
python3 -m pip install -r requirements.txt
```

After activating the virtual environment and installing the requirements, you’ll be able to run the BPF-related scripts and tools in this project.

## Running the Scripts

To run the monitoring script, you must have root privileges. To run the script, use the following command to monitor all system calls supported for all processes running on the system:

```bash
sudo su
source .venv/bin/activate
export PYTHONPATH=$(dirname `find /usr/lib -name bcc`):$PYTHONPATH
python3 ./main.py all
```

To monitor a specific system process or command, use the following command:

```bash
python3 ./main.py <command>
```

## Opening the Web Interface
To open the visualization of the allocations, follow the instructions in [frontend/README.md](frontend/README.md).

## Testing Programs

We provide a simple program for each supported system call to test the monitoring script. To run the test programs for a specific system call, use the following command:

```bash
./<system_call>/test_program.py
```

For example, to test the `mmap` system call, use the following command:
    
```bash
sudo ./main.py ./mmap/test_program.py
```

## Supported System Calls

The following system calls are supported by the monitoring script:
- `mmap`
- `munmap`
- `mremap`
- `brk`
