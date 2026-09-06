"""Private process, locking and atomic-file operations."""

from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import os
from pathlib import Path
import stat
import subprocess
import secrets
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


@contextmanager
def directory_fd(path: Path, *, create: bool = False):
    """Walk absolute directories without following links; hold each opened inode.

    All later reads, replacement and metadata operations are relative to this
    descriptor, so swapping an ancestor cannot redirect a privileged operation.
    """
    if not path.is_absolute() or ".." in path.parts:
        raise RunnerError("managed paths must be absolute without traversal")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            if create:
                try:
                    os.mkdir(part, 0o755, dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    pass
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=fd,
            )
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


@contextmanager
def regular_file(parent: int, name: str):
    fd = os.open(
        name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
    )
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RunnerError("managed file has an unexpected type or hard links")
        with os.fdopen(fd, "r", closefd=False) as stream:
            yield stream, info
    finally:
        os.close(fd)


def read_managed(path: Path) -> str:
    try:
        with directory_fd(path.parent) as parent:
            with regular_file(parent, path.name) as (stream, _):
                return stream.read()
    except FileNotFoundError:
        return ""


def ensure_directory(path: Path, *, mode: int, uid: int, gid: int) -> None:
    with directory_fd(path, create=True) as fd:
        info = os.fstat(fd)
        if info.st_uid not in (os.geteuid(), uid):
            raise RunnerError("managed directory has an unexpected owner")
        if (info.st_uid, info.st_gid) != (uid, gid):
            os.fchown(fd, uid, gid)
        if stat.S_IMODE(info.st_mode) != mode:
            os.fchmod(fd, mode)
        os.fsync(fd)


def remove_managed_file(path: Path, before_change=None) -> bool:
    try:
        with directory_fd(path.parent) as parent:
            with regular_file(parent, path.name):
                pass
            if before_change is not None:
                before_change()
            # unlink never follows the final name, even if it was replaced.
            os.unlink(path.name, dir_fd=parent)
            os.fsync(parent)
            return True
    except FileNotFoundError:
        return False


def atomic_write(
    path: Path,
    content: str,
    *,
    mode: int,
    uid: int,
    gid: int,
    before_change: Callable[[], None] | None = None,
) -> bool:
    with directory_fd(path.parent, create=True) as parent:
        try:
            with regular_file(parent, path.name) as (stream, current):
                if current.st_uid not in (os.geteuid(), uid):
                    raise RunnerError("managed file has an unexpected owner")
                if (
                    stream.read() == content
                    and stat.S_IMODE(current.st_mode) == mode
                    and current.st_uid == uid
                    and current.st_gid == gid
                ):
                    return False
        except FileNotFoundError:
            pass
        if before_change is not None:
            before_change()
        temporary = ".runnerctl-" + secrets.token_hex(16)
        fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=parent,
        )
        try:
            with os.fdopen(fd, "w") as stream:
                stream.write(content)
                stream.flush()
                os.fchown(stream.fileno(), uid, gid)
                os.fchmod(stream.fileno(), mode)
                os.fsync(stream.fileno())
            os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
    return True


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
