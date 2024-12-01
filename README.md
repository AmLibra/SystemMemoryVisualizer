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

This project uses a Python virtual environment for dependency management. To activate it, use the following command:

```bash
source ./bpfvenv/bin/activate
```

After activating the virtual environment, you’ll be able to run the BPF-related scripts and tools in this project.


## Running the Scripts

To run the monitoring script, you must have root privileges. To run the script, use the following command to monitor all system calls supported for all processes running on the system:

```bash
sudo ./main.py all 
```

To monitor a specific system process or command, use the following command:

```bash
sudo ./main.py <command>
```

## Testing programs

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
