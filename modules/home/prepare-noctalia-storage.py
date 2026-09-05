"""One-time file-key transition; never decrypt, print keys, or discard old state."""

import argparse
import fcntl
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import tempfile
import tomllib


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def safe_path(path):
    for part in (path, *path.parents):
        require(not part.is_symlink(), "Resolve symlinked Noctalia storage paths first")


def validate(config, state, cache, key):
    for path in (config, state, cache, key):
        safe_path(path)
    for path in [*config.glob("*.toml"), state / "settings.toml"]:
        if not path.exists():
            continue
        with path.open("rb") as stream:
            data = tomllib.load(stream)
        require(
            not data.get("include"),
            "Review included Noctalia config before file-key migration",
        )
        storage = data.get("storage", {})
        require(
            storage.get("key_source", "file") == "file"
            and storage.get("key_file", str(key)) == str(key),
            "Remove conflicting Noctalia storage overrides before deployment",
        )
        calendar = data.get("calendar", {})
        require(
            not calendar.get("enabled", False) and not calendar.get("accounts", []),
            "Review Noctalia calendar accounts before enabling passwordless startup",
        )
    for variable in (
        "NOCTALIA_CONFIG_HOME",
        "NOCTALIA_STATE_HOME",
        "NOCTALIA_DATA_HOME",
    ):
        require(
            not os.environ.get(variable),
            "Custom Noctalia roots require an explicit migration review",
        )
    for path in (
        key.parent,
        key,
        key.parent / "ready",
        key.parent / "pending",
        key.parent / "lock",
    ):
        safe_path(path)
        if path.exists():
            info = path.stat()
            if path == key.parent:
                require(
                    stat.S_ISDIR(info.st_mode),
                    "Expected a key directory, found a file; preserve it and choose a separate managed directory",
                )
            require(
                stat.S_ISDIR(info.st_mode)
                if path == key.parent
                else stat.S_ISREG(info.st_mode),
                "Noctalia key state has an unexpected file type",
            )
            require(
                info.st_uid == os.getuid(),
                "Noctalia key state must belong to the login user",
            )
            require(
                stat.S_IMODE(info.st_mode) == (0o700 if path == key.parent else 0o600),
                "Noctalia key directory/files require permissions 0700/0600",
            )
    if key.exists():
        require(
            key.is_file() and key.stat().st_size == 64,
            "Existing Noctalia key has unexpected metadata; refusing replacement",
        )
    if (key.parent / "ready").exists():
        require(
            key.exists(),
            "Noctalia key is missing; restore it, never generate a replacement",
        )
    elif not (key.parent / "pending").exists():
        require(not key.exists(), "Unmanaged Noctalia key requires operator review")


def archives(state, cache):
    return [
        (state / "clipboard", state / "clipboard.before-file-key"),
        (cache / "calendar", cache / "calendar.before-file-key"),
    ]


def preflight(config, state, cache, key, running):
    validate(config, state, cache, key)
    if (key.parent / "ready").exists():
        require(
            (config / "storage.toml").exists() or not running(),
            "Finish Noctalia file-key activation before starting the shell",
        )
        return
    require(
        not running(),
        "Stop noctalia.service before first migration; Hyprland may remain running",
    )
    pending = (key.parent / "pending").exists()
    for source, archive in archives(state, cache):
        safe_path(source)
        safe_path(archive)
        require(
            not archive.exists() or (pending and not source.exists()),
            "Noctalia archive collision; preserve both paths and resolve manually",
        )
        require(
            not source.exists() or source.is_dir(), "Expected a Noctalia data directory"
        )


def publish(path, contents):
    # Hard-link publication is atomic and cannot overwrite an existing key.
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
    sync_directory(path.parent)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def prepare(config, state, cache, key, running, apply=False):
    preflight(config, state, cache, key, running)
    if not apply:
        return
    key.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(key.parent / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        preflight(config, state, cache, key, running)
        ready, pending = key.parent / "ready", key.parent / "pending"
        if ready.exists():
            if pending.exists():
                pending.unlink()
                sync_directory(key.parent)
            return
        if not pending.exists():
            publish(pending, b"file-key-v1\n")
        for source, archive in archives(state, cache):
            if source.exists():
                source.rename(archive)
                sync_directory(source.parent)
        if not key.exists():
            publish(key, secrets.token_hex(32).encode("ascii"))
        publish(ready, b"file-key-v1\n")
        pending.unlink()
        sync_directory(key.parent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "state", "cache", "key"):
        parser.add_argument("--" + name, type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    def running():
        result = subprocess.run(
            ["/usr/bin/pgrep", "-u", str(os.getuid()), "-x", "noctalia"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        require(
            result.returncode in (0, 1), "Unable to check whether Noctalia is running"
        )
        return result.returncode == 0

    try:
        prepare(args.config, args.state, args.cache, args.key, running, args.apply)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, ValueError):
        # Avoid serializing TOML values or secret contents in diagnostics.
        print(
            "Noctalia storage preparation failed. Check desktop-session.md recovery instructions.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
