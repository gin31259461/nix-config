"""Converge SearXNG."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import traceback


class Conflict(Exception):
    """A safe diagnostic that never contains runtime configuration values."""


def execute(
    *argv: str, allow_failure: bool = False
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv, text=True, capture_output=True, timeout=60, check=not allow_failure
        )
    except subprocess.TimeoutExpired as error:
        raise Conflict(f"command timed out: {argv[0]}") from error
    except subprocess.CalledProcessError as error:
        raise Conflict(f"command failed ({error.returncode}): {argv[0]}") from None


class Searxng:
    def __init__(self, desired: dict[str, object], root: Path = Path("/"), run=execute):
        self.desired = desired
        self.root = root
        self.run = run

    def path(self, key: str) -> Path:
        value = self.desired[key]
        if (
            not isinstance(value, str)
            or not value.startswith("/")
            or ".." in Path(value).parts
        ):
            raise Conflict("invalid SearXNG manifest path")
        return self.root / value.lstrip("/")

    def preflight(self) -> None:
        pass

    def write_unit(self) -> bool:
        path = self.path("unitPath")
        receipt = self.path("receipt")
        unit = self.desired.get("unit")
        if not isinstance(unit, str):
            raise Conflict("SearXNG unit is invalid")
        if path.exists() and (
            path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1
        ):
            raise Conflict("SearXNG unit has conflicting type")
        if path.exists() and not receipt.exists() and path.read_text() != unit:
            raise Conflict("existing SearXNG unit requires removal before adoption")
        if (
            path.exists()
            and path.read_text() == unit
            and stat.S_IMODE(path.stat().st_mode) == 0o644
        ):
            return False
        self.path("pending").touch()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.pending")
        temporary.write_text(unit)
        temporary.chmod(0o644)
        os.replace(temporary, path)
        return True

    def wait_for_readiness(self) -> None:
        curl = self.desired.get("curl")
        endpoint = self.desired.get("endpoint")
        if not isinstance(curl, str) or not Path(curl).is_file():
            raise Conflict("SearXNG curl probe is missing")
        if not isinstance(endpoint, str) or not endpoint.startswith(
            "http://127.0.0.1:"
        ):
            raise Conflict("SearXNG endpoint is invalid")
        for query in ("test", "SearXNG", "readiness"):
            response = self.run(
                curl,
                "--fail",
                "--silent",
                "--show-error",
                "--retry",
                "10",
                "--retry-all-errors",
                "--retry-delay",
                "1",
                "--max-time",
                "20",
                "--get",
                "--data-urlencode",
                f"q={query}",
                "--data",
                "format=json",
                f"{endpoint}/search",
            )
            try:
                body = json.loads(response.stdout)
            except (json.JSONDecodeError, TypeError) as error:
                raise Conflict("SearXNG returned invalid JSON") from error
            if not isinstance(body, dict) or not isinstance(body.get("results"), list):
                raise Conflict("SearXNG response is invalid")
            if body["results"]:
                return
        raise Conflict("SearXNG returned no readiness results")

    def converge(self) -> None:
        if not self.desired.get("enabled"):
            return
        retry = self.path("pending").exists()
        changed = self.write_unit()
        if changed:
            self.run("systemctl", "daemon-reload")

        service = "searxng.service"
        enabled_state = self.run(
            "systemctl", "is-enabled", "--quiet", service, allow_failure=True
        )
        active = self.run(
            "systemctl", "is-active", "--quiet", service, allow_failure=True
        )
        if enabled_state.returncode:
            self.run("systemctl", "enable", service)
        if active.returncode:
            self.run("systemctl", "start", service)
        elif changed or retry:
            self.run("systemctl", "restart", service)

        self.wait_for_readiness()
        self.path("receipt").touch()
        self.path("pending").unlink(missing_ok=True)


def main() -> int:
    if (
        len(sys.argv) not in (3, 4)
        or sys.argv[2] not in ("preflight", "converge")
        or os.geteuid() != 0
    ):
        raise Conflict("private adapter must be invoked by arch-switch")
    if len(sys.argv) == 4 and sys.argv[3] != "--verbose":
        raise Conflict("private adapter received an invalid argument")
    desired = json.loads(Path(sys.argv[1]).read_text())
    Searxng(desired).preflight() if sys.argv[2] == "preflight" else Searxng(
        desired
    ).converge()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Conflict as error:
        print(f"SearXNG: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, ValueError, KeyError) as error:
        print(f"SearXNG failed: {type(error).__name__}", file=sys.stderr)
        if "--verbose" in sys.argv:
            traceback.print_exc()
        raise SystemExit(1) from error
