"""Converge the Arch Personal Agent without transporting runtime secrets."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import traceback


class Conflict(Exception):
    """A safe diagnostic that never contains runtime configuration values."""


class NotReady(Exception):
    """Required operator-owned configuration has never been prepared."""


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


class PersonalAgent:
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
            raise Conflict("invalid Personal Agent manifest path")
        return self.root / value.lstrip("/")

    def validate_file(self, key: str) -> Path:
        path = self.path(key)
        if path.is_symlink() or not path.is_file():
            raise Conflict(f"Personal Agent {key} must be a regular file")
        info = path.stat()
        if info.st_nlink != 1 or info.st_uid != 0 and self.root == Path("/"):
            raise Conflict(f"Personal Agent {key} has unsafe ownership")
        if stat.S_IMODE(info.st_mode) & 0o022:
            raise Conflict(f"Personal Agent {key} is writable by an unsafe identity")
        return path

    def validate_secrets(self, path: Path) -> None:
        keys: set[str] = set()
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = re.fullmatch(r"(DISCORD_TOKEN|NOTION_TOKEN)=(.+)", stripped)
            if not match or match.group(1) in keys:
                raise Conflict("Personal Agent secret configuration is invalid")
            keys.add(match.group(1))
        if keys != {"DISCORD_TOKEN", "NOTION_TOKEN"}:
            raise Conflict("Personal Agent secret configuration is incomplete")

    def preflight(self) -> None:
        if not self.desired.get("enabled"):
            return
        missing = [key for key in ("config", "secrets") if not self.path(key).exists()]
        if missing:
            if self.path("receipt").exists():
                raise Conflict(
                    "prepared Personal Agent runtime configuration is missing"
                )
            raise NotReady("runtime configuration is not prepared")
        config = self.validate_file("config")
        secrets = self.validate_file("secrets")
        self.validate_secrets(secrets)
        executable = self.desired.get("executable")
        if not isinstance(executable, str) or not Path(executable).is_file():
            raise Conflict("Personal Agent executable is missing")
        self.run(executable, "check-config", "--config", str(config))
        self.run(
            executable,
            "check-runtime",
            "--config",
            str(config),
            "--env-file",
            str(secrets),
        )
        self.account(create=False)

    def account(self, create: bool) -> None:
        group = self.run("getent", "group", "personal-agent", allow_failure=True)
        account = self.run("getent", "passwd", "personal-agent", allow_failure=True)
        if account.returncode == 0:
            if group.returncode:
                raise Conflict("existing Personal Agent account has no dedicated group")
            fields = account.stdout.strip().split(":")
            if len(fields) != 7 or fields[5:] != [
                "/var/lib/personal-agent",
                "/usr/bin/nologin",
            ]:
                raise Conflict(
                    "existing Personal Agent account has conflicting identity"
                )
            primary = self.run("id", "-gn", "personal-agent").stdout.strip()
            if primary != "personal-agent":
                raise Conflict(
                    "existing Personal Agent account has conflicting primary group"
                )
            return
        if not create:
            return
        if group.returncode:
            self.run("groupadd", "--system", "personal-agent")
        self.run(
            "useradd",
            "--system",
            "--gid",
            "personal-agent",
            "--home-dir",
            "/var/lib/personal-agent",
            "--shell",
            "/usr/bin/nologin",
            "personal-agent",
        )

    def write_unit(self) -> bool:
        path = self.path("unitPath")
        receipt = self.path("receipt")
        unit = self.desired.get("unit")
        if not isinstance(unit, str):
            raise Conflict("Personal Agent unit is invalid")
        if path.exists() and (
            path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1
        ):
            raise Conflict("Personal Agent unit has conflicting type")
        if path.exists() and not receipt.exists() and path.read_text() != unit:
            raise Conflict(
                "existing Personal Agent unit requires removal before adoption"
            )
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

    def ensure_metadata(self, path: Path, user: str, group: str, mode: int) -> None:
        info = path.stat()
        desired = f"{user}:{group}"
        if self.root == Path("/"):
            current = self.run("stat", "-c", "%U:%G", str(path)).stdout.strip()
            if current != desired:
                self.run("chown", desired, str(path))
        if stat.S_IMODE(info.st_mode) != mode:
            self.run("chmod", f"{mode:04o}", str(path))

    def converge(self) -> None:
        if not self.desired.get("enabled"):
            return
        self.preflight()
        retry = self.path("pending").exists()
        self.path("pending").touch()
        self.account(create=True)
        state = self.path("state")
        self.run(
            "install",
            "-d",
            "-m0750",
            "-o",
            "personal-agent",
            "-g",
            "personal-agent",
            str(state),
        )
        self.ensure_metadata(self.path("config"), "root", "personal-agent", 0o640)
        self.ensure_metadata(self.path("secrets"), "root", "root", 0o600)
        changed = self.write_unit()
        if changed:
            self.run("systemctl", "daemon-reload")
        enabled = self.run(
            "systemctl",
            "is-enabled",
            "--quiet",
            "personal-agent.service",
            allow_failure=True,
        )
        active = self.run(
            "systemctl",
            "is-active",
            "--quiet",
            "personal-agent.service",
            allow_failure=True,
        )
        if enabled.returncode:
            self.run("systemctl", "enable", "personal-agent.service")
        if active.returncode:
            self.run("systemctl", "start", "personal-agent.service")
        elif changed or retry:
            self.run("systemctl", "restart", "personal-agent.service")
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
    PersonalAgent(desired).preflight() if sys.argv[2] == "preflight" else PersonalAgent(
        desired
    ).converge()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NotReady as error:
        print(f"Personal Agent not ready: {error}", file=sys.stderr)
        raise SystemExit(20) from None
    except Conflict as error:
        print(f"Personal Agent: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, ValueError, KeyError) as error:
        print(f"Personal Agent failed: {type(error).__name__}", file=sys.stderr)
        if "--verbose" in sys.argv:
            traceback.print_exc()
        raise SystemExit(1) from error
