"""Command line tool to distribute jobs read from stdin onto GPUs."""
import argparse
import threading
import subprocess
import sys
import os
import time
from typing import List, Dict, Optional
from pathlib import Path


class GPUManager:
    """GPU manager, keeps track which GPUs used and which are avaiable."""

    def __init__(self, available_gpus: List[str], max_job_gpu: int):

        self.semaphore = threading.BoundedSemaphore(len(available_gpus))
        self.gpu_list_lock = threading.Lock()
        self.max_job_gpu = max_job_gpu

        self.available_gpus = list(available_gpus)
        self.available_gpus = [str(i) for i in self.available_gpus]
        self.job_per_gpu: Dict[str:int] = {}
        for i in self.available_gpus:
            self.job_per_gpu[i] = 0
        print()

    def get_any_available_gpu(self) -> Optional[str]:
        for id_, n_jobs in self.job_per_gpu.items():
            if n_jobs < self.max_job_gpu:
                return id_
        return None

    def allocate_job(self, command: str):
        gpu = self.get_any_available_gpu()
        if not gpu:
            print("No GPU is available now")
            return False
        print(f"GPU{gpu} is available to run {command}")
        self.run_command_with_gpu(command, gpu)
        self.job_per_gpu[gpu] += 1
        return True

    def run_command_with_gpu(self, command: str, gpu: str):

        myenv = os.environ.copy()
        myenv["CUDA_VISIBLE_DEVICES"] = str(gpu)

        def run_then_release_GPU(command, gpu):
            myenv = os.environ.copy()
            myenv["CUDA_VISIBLE_DEVICES"] = str(gpu)
            proc = subprocess.Popen(args=command, shell=True, env=myenv)
            proc.wait()
            self.job_per_gpu[gpu] -= 1
            return

        thread = threading.Thread(target=run_then_release_GPU, args=(command, gpu))
        thread.start()
        # returns immediately after the thread starts
        return thread


def read_commands_and_run(gpu_manager, commands_files: Path):
    """Read commands from stdin and run them on gpus from the gpu manager.

    Args:
        gpu_manager: A GPUManager instance

    """
    with open(commands_files, "r") as fp:
        # Make sure that we don't keep this file open or we can't edit it while the scheduler is running
        lines = fp.readlines()
    lines = [i.rstrip() for i in lines]  # Clean up the white spaces
    # Divide list into chunks
    current_index = 0
    while current_index < len(lines):
        command = lines[current_index]
        if gpu_manager.allocate_job(command):
            current_index += 1
            continue
        time.sleep(10)


def main():
    """Read command line arguments and start reading from stdin."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpus", nargs="+", type=str, required=True)
    parser.add_argument("--commands_file", type=str, required=True)
    parser.add_argument("--jobs_per_gpu", type=int, required=True)
    args = parser.parse_args()
    assert Path(args.commands_file).exists(), f"Could not find {args.commands_file}"

    # Support both comma separated and individually passed GPU ids
    gpus = args.gpus if len(args.gpus) > 1 else args.gpus[0].split(",")
    gpu_manager = GPUManager(gpus, args.jobs_per_gpu)
    read_commands_and_run(gpu_manager, commands_files=args.commands_file)


if __name__ == "__main__":
    main()
