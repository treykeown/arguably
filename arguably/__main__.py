#!/usr/bin/env python3

import multiprocessing
import queue
import sys
from pathlib import Path
from typing import List

import arguably
from arguably.util import load_and_run, LoadAndRunResult


args_for_file: List[str] = []


@arguably.command
def main(file: Path, *args: str) -> None:
    """
    run functions from any python file
    :param file: the file to load
    :param args: the function to run, and any arguments
    """

    # Check that the user-specified file exists
    file = file.expanduser()
    if not file.exists():
        arguably.error(f"file {str(file)} does not exist")

    # Set up multiprocessing so we can launch a new process to load the file
    # A result object will be passed back in the queue
    multiprocessing.set_start_method("spawn")
    results_queue: multiprocessing.Queue[LoadAndRunResult] = multiprocessing.Queue()
    proc = multiprocessing.Process(target=load_and_run, args=(results_queue, file, args_for_file))

    # Run the external process
    proc.start()
    proc.join()

    # Check the results
    try:
        result = results_queue.get(timeout=0)
    except queue.Empty:
        arguably.error("no results from launched process")
    else:
        if result.error:
            arguably.error(result.error)
        elif result.exception:
            raise result.exception


if __name__ == "__main__":
    # We strip off the rest of the arguments - if we were doing things normally, this wouldn't be required - however,
    # we're effectively adding a subcommand without telling argparse, which will cause issues if there are any --options
    # passed in.
    if len(sys.argv) > 2:
        args_for_file = sys.argv[2:]
        del sys.argv[2:]

    # Run it
    arguably.run(name="arguably")
