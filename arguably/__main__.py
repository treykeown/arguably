#!/usr/bin/env python3
import multiprocessing
import queue
import sys
from pathlib import Path
from typing import List

import arguably
from ._util import load_and_run, LoadAndRunResult, run_redirected_io

args_for_file: List[str] = []
argv_cut_index = 2


@arguably.command
def main(file: Path, *args: str, debug: bool = False, no_warn: bool = False) -> None:
    """
    run functions from any python file

    Args:
        file: the file to load
        *args: the function to run, as well as any arguments
        debug: if set, will show a debug log for how argparse is set up and for how functions are called
        no_warn: if set, will not show warnings
    """

    # Check that the user-specified file exists
    file = file.expanduser()
    if not file.exists():
        arguably.error(f"file {str(file)} does not exist")

    # Prepare argv for the invocation of arguably in the subprocess
    del sys.argv[:1]  # Remove argv[0] - the filename becomes argv[0].
    if debug:
        sys.argv.remove("--debug")
    if no_warn:
        sys.argv.remove("--no-warn")

    # Run `load_and_run` on the file in a spawned process
    mp_ctx = multiprocessing.get_context("spawn")
    results_queue: multiprocessing.Queue[LoadAndRunResult] = mp_ctx.Queue()
    run_redirected_io(mp_ctx, load_and_run, (results_queue, file, args_for_file, debug, no_warn))

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
    if "--no-warn" in sys.argv[1 : argv_cut_index + 1]:
        argv_cut_index += 1
    if len(sys.argv) > argv_cut_index:
        args_for_file = sys.argv[argv_cut_index:]
        del sys.argv[argv_cut_index:]

    # Run it
    arguably.run(name="arguably")
