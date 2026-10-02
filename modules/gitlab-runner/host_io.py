"""Private process, locking and atomic-file operations."""

from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from nix_adapter.io import (
    atomic_write,
    directory_fd,
    ensure_directory,
    read_managed,
    regular_file,
    remove_managed_file,
)
from nix_adapter.lock import operation_lock as _operation_lock
from runner_model import RunnerError, ranges_overlap

__all__ = [
    "HostPaths",
    "RunnerError",
    "atomic_write",
    "directory_fd",
    "ensure_directory",
    "ensure_subordinate_range",
    "operation_lock",
    "os",
    "ranges_overlap",
    "read_managed",
    "regular_file",
    "remove_managed_file",
    "run",
]


@dataclass(frozen=True)
class HostPaths:
    """Private filesystem seam; production paths cannot be overridden by CLI."""

    subuid: Path = Path("/etc/subuid")
    subgid: Path = Path("/etc/subgid")
    runtime: Path = Path("/run/user")


def run(
    argv: list[str],
    *,
    check: bool = True,
    capture: bool = False,
    env: dict[str, str] | None = None,
    timeout: float = 300,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            argv,
            check=False,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RunnerError(f"command timed out after {timeout}s: {argv[0]}") from None
    if check and result.returncode != 0:
        raise RunnerError(
            f"command failed with exit code {result.returncode}: {argv[0]}"
        )
    return result


@contextmanager
def operation_lock(path: Path = Path("/run/lock/nix-config-runner.lock")):
    """Serialize our mutations across instances, including shared sub-ID files."""
    with _operation_lock(path, label="Runner operation"):
        yield


def ensure_subordinate_range(
    path: Path,
    user: str,
    desired: dict[str, int],
) -> None:
    lines = read_managed(path).splitlines()
    user_indices: list[int] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split(":")
        if len(fields) != 3 or not fields[1].isdigit() or not fields[2].isdigit():
            raise RunnerError(f"invalid subordinate ID allocation in {path}")
        existing_user, start_text, count_text = fields
        if existing_user == user:
            user_indices.append(index)
            continue
        existing = {"start": int(start_text), "count": int(count_text)}
        if ranges_overlap(desired, existing):
            raise RunnerError(
                f"desired subordinate ID range for {user} overlaps {existing_user} in {path}"
            )

    if len(user_indices) > 1:
        raise RunnerError(
            f"multiple subordinate ID allocations exist for {user} in {path}"
        )
    desired_line = f"{user}:{desired['start']}:{desired['count']}"
    if user_indices:
        lines[user_indices[0]] = desired_line
    else:
        lines.append(desired_line)
    atomic_write(path, "\n".join(lines) + "\n", mode=0o644, uid=0, gid=0)
