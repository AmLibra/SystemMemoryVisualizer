import subprocess
import os
from tracers.common import RED, GREEN, END

class Runner:
    def __init__(self):
        self.process = None

    def run_command(self, command: list) -> int:
        """
        Runs a command and returns its PID.
        """
        if not command:
            raise ValueError("No command provided to run.")

        print(f"{GREEN}Starting process: {' '.join(command)}{END}")
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"{GREEN}Started process: {command[0]} with PID: {self.process.pid}{END}")
        return self.process.pid

    def wait_for_exit(self):
        """
        Waits for the process to exit and captures its return code.
        """
        if self.process is None:
            raise ValueError("No process is currently running.")
        try:
            self.process.wait()
            print(f"{RED}Process {self.process.pid} exited with return code: {self.process.returncode}{END}")
        except KeyboardInterrupt:
            print(f"{RED}Process {self.process.pid} interrupted. Killing process.{END}")
            self.process.terminate()

    def cleanup(self):
        """
        Ensures the process is terminated if still running.
        """
        if self.process is not None and self.process.poll() is None:
            print(f"{RED}Cleaning up process {self.process.pid}.{END}")
            self.process.terminate()

    @staticmethod
    def is_valid_pid(pid: int) -> bool:
        """
        Check if a given PID is valid and the process exists.
        """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
