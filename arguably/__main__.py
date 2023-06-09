#!/usr/bin/env python3
import multiprocessing
import queue
import sys
from pathlib import Path
from typing import List

import arguably
from arguably.util import load_and_run, LoadAndRunResult

args_for_file: List[str] = []
argv_cut_index = 2


@arguably.command
def main(file: Path, *args: str, debug: bool = False) -> None:
    """
    run functions from any python file
    :param file: the file to load
    :param args: the function to run, and any arguments
    :param debug: show a debug log for how argparse is set up and for how functions are called
    """

    # Check that the user-specified file exists
    file = file.expanduser()
    if not file.exists():
        arguably.error(f"file {str(file)} does not exist")

    # Set up multiprocessing so we can launch a new process to load the file
    # A result object will be passed back in the queue
    multiprocessing.set_start_method("spawn")
    results_queue: multiprocessing.Queue[LoadAndRunResult] = multiprocessing.Queue()
    proc = multiprocessing.Process(target=load_and_run, args=(results_queue, file, args_for_file, debug))

    # Prepare argv for the invocation of arguably in the subprocess
    del sys.argv[:1]  # Remove argv[0] - the filename becomes argv[0].
    if debug:
        sys.argv.remove("--debug")

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
    if "--debug" in sys.argv[1 : argv_cut_index + 1]:
        argv_cut_index += 1
    if len(sys.argv) > argv_cut_index:
        args_for_file = sys.argv[argv_cut_index:]
        del sys.argv[argv_cut_index:]

    # Run it
    arguably.run(name="arguably")
