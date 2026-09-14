"""Public arch-switch CLI boundary; privileged mutations remain in the shell backend."""

from __future__ import annotations

import os
from pathlib import Path
import sys

USAGE = "usage: arch-switch [--check | --update] [--verbose]"


def normalize(arguments: list[str]) -> list[str] | None:
    check = False
    update = False
    verbose = False
    for argument in arguments:
        if argument == "--help":
            return None
        if argument == "--check":
            check = True
        elif argument == "--update":
            update = True
        elif argument == "--verbose":
            verbose = True
        else:
            raise ValueError(USAGE)
    if check and update:
        raise ValueError(USAGE)
    result: list[str] = []
    if check:
        result.append("--check")
    if update:
        result.append("--update")
    if verbose:
        result.append("--verbose")
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print(USAGE, file=sys.stderr)
        return 2
    backend = Path(sys.argv[1])
    try:
        arguments = normalize(sys.argv[2:])
    except ValueError:
        print(USAGE, file=sys.stderr)
        return 2
    if arguments is None:
        print(USAGE)
        return 0
    os.execv(backend, [str(backend), *arguments])
    raise AssertionError("execv returned unexpectedly")


if __name__ == "__main__":
    raise SystemExit(main())
