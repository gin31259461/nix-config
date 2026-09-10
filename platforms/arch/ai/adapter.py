"""Privileged AI adapter entrypoint with explicit optional readiness status."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).parents[1] / "system"))
import runtime
from files import Conflict
from native import Native

OPTIONAL_NOT_READY = 20


def _verbose() -> bool:
    return len(sys.argv) == 4 and sys.argv[3] == "--verbose"


def main() -> int:
    if (
        len(sys.argv) not in (3, 4)
        or sys.argv[2] not in ("preflight", "converge")
        or (len(sys.argv) == 4 and sys.argv[3] != "--verbose")
        or os.geteuid() != 0
    ):
        raise Conflict("private AI adapter must be invoked by arch-switch")
    if _verbose():
        os.environ["NIX_CONFIG_VERBOSE"] = "1"
    runtime.Native = Native
    ai = runtime.AI(json.loads(Path(sys.argv[1]).read_text()))
    phase = sys.argv[2]
    if phase == "preflight":
        ready = ai.preflight()
    else:
        ready = ai.preflight(installed=True)
        if ready:
            ai.converge()
    if ai.desired.get("llama") and not ready:
        return OPTIONAL_NOT_READY
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Conflict as error:
        print(f"AI services: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, ValueError, KeyError) as error:
        print(f"AI services failed: {type(error).__name__}: {error}", file=sys.stderr)
        if _verbose():
            traceback.print_exc()
        raise SystemExit(1) from error
