import importlib.util
import multiprocessing
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import arguably


@dataclass
class LoadAndRunResult:
    error: Optional[str] = None
    exception: Optional[BaseException] = None


def load_and_run(results: multiprocessing.Queue, file: Path, target_str: str, *args: str) -> None:
    # Load the specified file
    try:
        spec = importlib.util.spec_from_file_location("_arguably_imported", str(file))
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
    except BaseException as e:
        results.put(LoadAndRunResult(exception=e))
        return

    # Get the target function
    if not hasattr(module, target_str):
        results.put(LoadAndRunResult(error=f"file {str(file)} has no attribute {target_str}"))
        return
    target = getattr(module, target_str)

    # `target_str` becomes sys.argv[0]
    del sys.argv[:2]
    sys.argv.extend(*args)

    # Not required, but if arguably was used at all by the target script, we should reset the arguably context
    arguably._context.reset()

    # Set the target as the only command and run
    arguably.command(target)
    try:
        arguably.run()
    except BaseException as e:
        results.put(LoadAndRunResult(exception=e))
        return
    else:
        results.put(LoadAndRunResult())
        return
