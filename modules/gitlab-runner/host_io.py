"""Private process, locking and atomic-file operations."""

from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from typing import Callable
from runner_model import RunnerError, ranges_overlap


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
    descriptor = os.open(
        path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600
    )
    try:
        entry = os.fstat(descriptor)
        if not stat.S_ISREG(entry.st_mode) or entry.st_uid != os.geteuid():
            raise RunnerError("Runner operation lock has an unexpected owner or type")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RunnerError("another Runner operation is running") from None
        yield
    finally:
        os.close(descriptor)


def atomic_write(
    path: Path,
    content: str,
    *,
    mode: int,
    uid: int,
    gid: int,
    before_change: Callable[[], None] | None = None,
) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = path.stat()
        if (
            path.read_text() == content
            and stat.S_IMODE(current.st_mode) == mode
            and current.st_uid == uid
            and current.st_gid == gid
        ):
            return False
    if before_change is not None:
        before_change()
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", dir=path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_path, mode)
        os.chown(temporary_path, uid, gid)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return True


def ensure_subordinate_range(
    path: Path,
    user: str,
    desired: dict[str, int],
) -> None:
    lines = path.read_text().splitlines() if path.exists() else []
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
