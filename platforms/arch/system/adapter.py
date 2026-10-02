"""Privileged Arch system-settings adapter entrypoint."""

from __future__ import annotations

from nix_adapter import run_adapter_cli
import runtime


def main() -> int:
    return run_adapter_cli(
        lambda desired: runtime.System(desired),
        name="System settings",
    )


if __name__ == "__main__":
    raise SystemExit(main())
