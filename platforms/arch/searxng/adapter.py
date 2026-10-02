"""Converge SearXNG."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from nix_adapter import BaseServiceAdapter, Conflict, Native, run_adapter_cli


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


class _AdapterRunner(Native):
    def __init__(self, adapter: Searxng):
        super().__init__()
        self._adapter = adapter

    def run(
        self, *argv: str, check: bool = True, **kwargs
    ) -> subprocess.CompletedProcess[str]:
        return self._adapter.run(*argv, allow_failure=not check)


class Searxng(BaseServiceAdapter):
    def __init__(self, desired: dict[str, object], root: Path = Path("/"), run=execute):
        self.run = run
        super().__init__(desired=desired, root=root, runner=_AdapterRunner(self))

    def preflight(self) -> None:
        pass

    def write_unit(
        self,
        path: Path | None = None,
        unit: str | None = None,
        receipt: Path | None = None,
        pending: Path | None = None,
        mode: int = 0o644,
    ) -> bool:
        p = path or self.path("unitPath")
        u = unit if unit is not None else self.desired.get("unit")
        if not isinstance(u, str):
            raise Conflict("SearXNG unit is invalid")
        r = receipt or self.path("receipt")
        pend = pending or self.path("pending")
        return super().write_unit(p, u, r, pend, mode=mode)

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
            self.systemd.daemon_reload()

        service = "searxng.service"
        if not self.systemd.is_enabled(service):
            self.systemd.enable(service)
        if not self.systemd.is_active(service):
            self.systemd.start(service)
        elif changed or retry:
            self.systemd.restart(service)

        self.wait_for_readiness()
        self.path("receipt").touch()
        self.path("pending").unlink(missing_ok=True)


def main() -> int:
    return run_adapter_cli(
        lambda desired: Searxng(desired),
        name="SearXNG",
    )


if __name__ == "__main__":
    raise SystemExit(main())
