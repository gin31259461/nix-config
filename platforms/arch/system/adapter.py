"""Privileged Arch system-settings adapter entrypoint."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback

import runtime
from files import Conflict
from native import Native


def _verbose() -> bool:
    return len(sys.argv) == 4 and sys.argv[3] == "--verbose"


def main() -> int:
    if (
        len(sys.argv) not in (3, 4)
        or sys.argv[2] not in ("preflight", "converge")
        or (len(sys.argv) == 4 and sys.argv[3] != "--verbose")
        or os.geteuid() != 0
    ):
        raise Conflict("private adapter must be invoked by arch-switch")
    if _verbose():
        os.environ["NIX_CONFIG_VERBOSE"] = "1"
    runtime.Native = Native
    system = runtime.System(json.loads(Path(sys.argv[1]).read_text()))
    if sys.argv[2] == "preflight":
        system.preflight()
    else:
        system.converge()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Conflict as error:
        print(f"System settings: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, ValueError, KeyError) as error:
        print(
            f"System settings failed: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        if _verbose():
            traceback.print_exc()
        raise SystemExit(1) from error
