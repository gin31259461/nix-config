#!/usr/bin/env python3

"""Converge dedicated rootless Podman GitLab Runner instances."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any


class RunnerError(RuntimeError):
    pass


def run(
    argv: list[str],
    *,
    check: bool = True,
    capture: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        env=env,
    )
    if check and result.returncode != 0:
        raise RunnerError(f"command failed with exit code {result.returncode}: {argv[0]}")
    return result


def require_root() -> None:
    if os.geteuid() != 0:
        raise RunnerError("this command must run as root")


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def toml_array(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def ranges_overlap(left: dict[str, int], right: dict[str, int]) -> bool:
    left_end = left["start"] + left["count"] - 1
    right_end = right["start"] + right["count"] - 1
    return left["start"] <= right_end and right["start"] <= left_end


def validate_instances(instances: dict[str, Any]) -> None:
    if not instances:
        raise RunnerError("at least one GitLab Runner instance is required")

    users: set[str] = set()
    service_names: set[str] = set()
    uids: set[int] = set()
    for instance_name, instance in instances.items():
        account = instance["account"]
        gitlab = instance["gitlab"]
        runner = instance["runner"]
        network = instance["network"]

        if not re.fullmatch(r"[a-z][a-z0-9-]*", instance_name):
            raise RunnerError(f"invalid instance name: {instance_name}")
        if not re.fullmatch(r"[a-z_][a-z0-9_-]*", account["user"]):
            raise RunnerError(f"invalid account name for {instance_name}")
        if account["user"] in users or runner["serviceName"] in service_names:
            raise RunnerError("Runner account and service names must be unique")
        if account["uid"] in uids:
            raise RunnerError("Runner account UIDs must be unique")
        users.add(account["user"])
        service_names.add(runner["serviceName"])
        uids.add(account["uid"])

        if account["home"] != f"/home/{account['user']}":
            raise RunnerError(f"{instance_name} must use its dedicated /home directory")
        if not gitlab["url"].startswith("https://"):
            raise RunnerError(f"{instance_name} GitLab URL must use HTTPS")
        for range_name in ("subUid", "subGid"):
            id_range = account[range_name]
            if id_range["start"] <= 0 or id_range["count"] <= 0:
                raise RunnerError(f"{instance_name} has an invalid {range_name} range")
        for image_name in ("managerImage", "defaultJobImage"):
            image = runner[image_name]
            if "/" not in image or ":" not in image or image.endswith(":latest"):
                raise RunnerError(f"{instance_name} {image_name} must be qualified and pinned")
        validation_image = instance["validation"]["image"]
        if "/" not in validation_image or ":" not in validation_image:
            raise RunnerError(f"{instance_name} validation image must be qualified and pinned")
        if runner["concurrent"] != 1:
            raise RunnerError(f"{instance_name} must remain a dedicated concurrent=1 stack")
        required_interface = network.get("requiredInterface")
        if required_interface is not None and not re.fullmatch(
            r"[A-Za-z0-9_.:-]+", required_interface
        ):
            raise RunnerError(f"{instance_name} has an invalid requiredInterface")

    names = sorted(instances)
    for index, left_name in enumerate(names):
        for right_name in names[index + 1 :]:
            left = instances[left_name]["account"]
            right = instances[right_name]["account"]
            for range_name in ("subUid", "subGid"):
                if ranges_overlap(left[range_name], right[range_name]):
                    raise RunnerError(
                        f"{left_name} and {right_name} have overlapping {range_name} ranges"
                    )


def select_instance(instances: dict[str, Any], name: str) -> dict[str, Any]:
    try:
        return instances[name]
    except KeyError as error:
        available = ", ".join(sorted(instances))
        raise RunnerError(f"unknown instance {name}; available: {available}") from error


def required_interface_is_up(name: str | None, ip_path: str) -> None:
    if name is None:
        return
    result = run(
        [ip_path, "-json", "link", "show", "dev", name], capture=True, check=False
    )
    if result.returncode != 0:
        raise RunnerError(f"required network interface is missing: {name}")
    links = json.loads(result.stdout)
    if len(links) != 1 or "UP" not in links[0].get("flags", []):
        raise RunnerError(f"required network interface is not up: {name}")


def ensure_account(instance: dict[str, Any]) -> pwd.struct_passwd:
    account = instance["account"]
    try:
        entry = pwd.getpwnam(account["user"])
    except KeyError:
        run(
            [
                "useradd",
                "--create-home",
                "--home-dir",
                account["home"],
                "--shell",
                "/bin/bash",
                "--uid",
                str(account["uid"]),
                "--user-group",
                account["user"],
            ]
        )
        run(["usermod", "--lock", account["user"]])
        entry = pwd.getpwnam(account["user"])

    if entry.pw_uid != account["uid"]:
        raise RunnerError(f"{account['user']} already exists with a different UID")
    if entry.pw_dir != account["home"]:
        raise RunnerError(f"{account['user']} already exists with a different home")
    return entry


def atomic_write(
    path: Path,
    content: str,
    *,
    mode: int,
    uid: int,
    gid: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as temporary:
        temporary.write(content)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.chmod(temporary_path, mode)
    os.chown(temporary_path, uid, gid)
    os.replace(temporary_path, path)


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
        raise RunnerError(f"multiple subordinate ID allocations exist for {user} in {path}")
    desired_line = f"{user}:{desired['start']}:{desired['count']}"
    if user_indices:
        lines[user_indices[0]] = desired_line
    else:
        lines.append(desired_line)
    atomic_write(path, "\n".join(lines) + "\n", mode=0o644, uid=0, gid=0)


def registration_metadata(config_path: Path) -> dict[str, str]:
    if not config_path.exists():
        return {}
    content = config_path.read_text()
    if len(re.findall(r"(?m)^\s*\[\[runners\]\]\s*$", content)) > 1:
        raise RunnerError("dedicated Runner config contains multiple registrations")
    metadata: dict[str, str] = {}
    patterns = {
        "id": r"(?m)^\s*id\s*=\s*(\S+)\s*$",
        "token": r'(?m)^\s*token\s*=\s*"([^"]+)"\s*$',
        "token_obtained_at": r"(?m)^\s*token_obtained_at\s*=\s*(\S+)\s*$",
        "token_expires_at": r"(?m)^\s*token_expires_at\s*=\s*(\S+)\s*$",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            metadata[key] = match.group(1)
    return metadata


def render_registration_template(instance: dict[str, Any]) -> str:
    runner = instance["runner"]
    dns = instance["network"].get("dns")
    lines = [
        "[[runners]]",
        f"  name = {toml_string(runner['name'])}",
        '  executor = "docker"',
        '  environment = ["FF_NETWORK_PER_BUILD=1"]',
        "",
        "  [runners.docker]",
        '    host = "unix:///run/podman/podman.sock"',
        f"    image = {toml_string(runner['defaultJobImage'])}",
        "    privileged = false",
        f"    cpus = {toml_string(runner['cpus'])}",
        f"    memory = {toml_string(runner['memory'])}",
        f"    shm_size = {runner['shmSizeBytes']}",
        f"    pull_policy = {toml_string(runner['pullPolicy'])}",
        '    volumes = ["/cache"]',
        f"    allowed_images = {toml_array(runner['allowedImages'])}",
        f"    allowed_services = {toml_array(runner['allowedServices'])}",
    ]
    if dns:
        lines.append(f"    dns = [{toml_string(dns)}]")
    return "\n".join(lines) + "\n"


def render_config(instance: dict[str, Any], metadata: dict[str, str]) -> str:
    runner = instance["runner"]
    if "token" not in metadata:
        return (
            f"concurrent = {runner['concurrent']}\n"
            "check_interval = 3\n"
            "shutdown_timeout = 30\n"
        )

    gitlab = instance["gitlab"]
    template = render_registration_template(instance).splitlines()
    lines = [
        f"concurrent = {runner['concurrent']}",
        "check_interval = 3",
        "shutdown_timeout = 30",
        "",
        "[[runners]]",
        f"  name = {toml_string(runner['name'])}",
        f"  url = {toml_string(gitlab['url'])}",
    ]
    if "id" in metadata:
        lines.append(f"  id = {metadata['id']}")
    lines.append(f"  token = {toml_string(metadata['token'])}")
    for field in ("token_obtained_at", "token_expires_at"):
        if field in metadata:
            lines.append(f"  {field} = {metadata[field]}")
    lines.extend(template[3:])
    return "\n".join(lines) + "\n"


def render_service(instance: dict[str, Any], uid: int, podman_path: str) -> str:
    account = instance["account"]
    runner = instance["runner"]
    runtime_dir = f"/run/user/{uid}"
    config_dir = f"{account['home']}/gitlab-runner/config"
    cache_dir = f"{account['home']}/gitlab-runner/cache"
    socket = f"{runtime_dir}/podman/podman.sock"
    dns_argument = ""
    if instance["network"].get("dns"):
        dns_argument = f"  --dns {instance['network']['dns']} \\\n"
    return f"""[Unit]
Description=GitLab Runner manager for {runner['name']}
Wants=network-online.target
After=network-online.target podman.socket
Requires=podman.socket

[Service]
Type=simple
Environment=XDG_RUNTIME_DIR={runtime_dir}
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path={runtime_dir}/bus
ExecStartPre=-{podman_path} rm --force {runner['serviceName']}
ExecStart={podman_path} run \\
  --rm \\
  --name {runner['serviceName']} \\
  --network host \\
  --security-opt label=disable \\
  --stop-signal SIGQUIT \\
  --volume {config_dir}:/etc/gitlab-runner:rw \\
  --volume {cache_dir}:/cache:rw \\
  --volume {socket}:/run/podman/podman.sock:rw \\
  --env DOCKER_HOST=unix:///run/podman/podman.sock \\
{dns_argument}  {runner['managerImage']} \\
  run \\
  --user=gitlab-runner \\
  --working-directory=/home/gitlab-runner
ExecStop=-{podman_path} stop --time 30 {runner['serviceName']}
ExecStopPost=-{podman_path} rm --force {runner['serviceName']}
Restart=always
RestartSec=5
TimeoutStartSec=120
TimeoutStopSec=45
Delegate=yes

[Install]
WantedBy=default.target
"""


def run_as(
    entry: pwd.struct_passwd,
    argv: list[str],
    *,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    runtime_dir = f"/run/user/{entry.pw_uid}"
    return run(
        [
            "runuser",
            "--user",
            entry.pw_name,
            "--",
            "env",
            f"HOME={entry.pw_dir}",
            f"XDG_RUNTIME_DIR={runtime_dir}",
            f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime_dir}/bus",
            *argv,
        ],
        capture=capture,
        check=check,
    )


def ensure_directories(entry: pwd.struct_passwd) -> tuple[Path, Path, Path]:
    root = Path(entry.pw_dir) / "gitlab-runner"
    config_dir = root / "config"
    cache_dir = root / "cache"
    unit_dir = Path(entry.pw_dir) / ".config/systemd/user"
    for path in (root, config_dir, cache_dir, unit_dir):
        path.mkdir(parents=True, exist_ok=True)
        os.chown(path, entry.pw_uid, entry.pw_gid)
        os.chmod(path, 0o700)
    return config_dir, cache_dir, unit_dir


def verify_rootless_podman(
    entry: pwd.struct_passwd,
    podman_path: str,
) -> None:
    version_result = run_as(entry, [podman_path, "--version"], capture=True)
    version_match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_result.stdout)
    if version_match is None or tuple(map(int, version_match.groups())) < (4, 2, 0):
        raise RunnerError("rootless Podman 4.2.0 or newer is required")
    info_result = run_as(
        entry,
        [podman_path, "info", "--format", "json"],
        capture=True,
    )
    info = json.loads(info_result.stdout)
    if not info.get("host", {}).get("security", {}).get("rootless", False):
        raise RunnerError(f"Podman is not rootless for {entry.pw_name}")
    if info.get("host", {}).get("networkBackend") != "netavark":
        raise RunnerError(f"Podman does not use netavark for {entry.pw_name}")


def reconcile(instance: dict[str, Any], platform: dict[str, str]) -> None:
    require_root()
    required_interface_is_up(instance["network"].get("requiredInterface"), platform["ip"])
    for executable in (platform["podman"], platform["ip"]):
        if not Path(executable).is_file():
            raise RunnerError(f"required host executable is missing: {executable}")

    entry = ensure_account(instance)
    account = instance["account"]
    ensure_subordinate_range(Path("/etc/subuid"), entry.pw_name, account["subUid"])
    ensure_subordinate_range(Path("/etc/subgid"), entry.pw_name, account["subGid"])
    verify_rootless_podman(entry, platform["podman"])
    config_dir, _, unit_dir = ensure_directories(entry)
    config_path = config_dir / "config.toml"
    metadata = registration_metadata(config_path)
    atomic_write(
        config_dir / "registration-template.toml",
        render_registration_template(instance),
        mode=0o600,
        uid=entry.pw_uid,
        gid=entry.pw_gid,
    )
    atomic_write(
        config_path,
        render_config(instance, metadata),
        mode=0o600,
        uid=entry.pw_uid,
        gid=entry.pw_gid,
    )
    service_name = instance["runner"]["serviceName"]
    atomic_write(
        unit_dir / f"{service_name}.service",
        render_service(instance, entry.pw_uid, platform["podman"]),
        mode=0o600,
        uid=entry.pw_uid,
        gid=entry.pw_gid,
    )

    run(["loginctl", "enable-linger", entry.pw_name])
    run(["systemctl", "start", f"user@{entry.pw_uid}.service"])
    run_as(entry, ["systemctl", "--user", "daemon-reload"])
    run_as(entry, ["systemctl", "--user", "enable", "--now", "podman.socket"])
    image = instance["runner"]["managerImage"]
    image_exists = run_as(
        entry,
        [platform["podman"], "image", "exists", image],
        capture=True,
        check=False,
    )
    if image_exists.returncode == 1:
        run_as(entry, [platform["podman"], "pull", image])
    elif image_exists.returncode != 0:
        raise RunnerError("unable to inspect the Runner manager image")
    run_as(entry, ["systemctl", "--user", "enable", "--now", f"{service_name}.service"])


def register(instance: dict[str, Any], platform: dict[str, str]) -> None:
    require_root()
    token = os.environ.get("GITLAB_RUNNER_TOKEN", "")
    if not (token.startswith("glrt-") or token.startswith("glrtr-")):
        raise RunnerError("GITLAB_RUNNER_TOKEN must contain a Runner authentication token")
    entry = pwd.getpwnam(instance["account"]["user"])
    config_path = Path(entry.pw_dir) / "gitlab-runner/config/config.toml"
    metadata = registration_metadata(config_path)
    if "token" in metadata:
        if metadata["token"] != token:
            raise RunnerError("the dedicated stack already contains a different registration")
        return

    service_name = instance["runner"]["serviceName"]
    runtime_dir = f"/run/user/{entry.pw_uid}"
    registration_env = os.environ.copy()
    registration_env.update(
        {
            "HOME": entry.pw_dir,
            "XDG_RUNTIME_DIR": runtime_dir,
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_dir}/bus",
            "CI_SERVER_URL": instance["gitlab"]["url"],
            "CI_SERVER_TOKEN": token,
            "REGISTER_NON_INTERACTIVE": "true",
        }
    )
    command = [
        "runuser",
        "--preserve-environment",
        "--user",
        entry.pw_name,
        "--",
        platform["podman"],
        "exec",
        "--env",
        "CI_SERVER_URL",
        "--env",
        "CI_SERVER_TOKEN",
        "--env",
        "REGISTER_NON_INTERACTIVE",
        service_name,
        "gitlab-runner",
        "register",
        "--template-config",
        "/etc/gitlab-runner/registration-template.toml",
    ]
    result = subprocess.run(
        command,
        env=registration_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise RunnerError("Runner registration failed; output was suppressed to protect the token")
    reconcile(instance, platform)


def verify(instance: dict[str, Any], platform: dict[str, str]) -> None:
    require_root()
    required_interface_is_up(instance["network"].get("requiredInterface"), platform["ip"])
    entry = pwd.getpwnam(instance["account"]["user"])
    socket_path = Path(f"/run/user/{entry.pw_uid}/podman/podman.sock")
    if not socket_path.exists() or not stat.S_ISSOCK(socket_path.stat().st_mode):
        raise RunnerError(f"rootless Podman socket is unavailable for {entry.pw_name}")
    service_name = instance["runner"]["serviceName"]
    run_as(entry, ["systemctl", "--user", "is-active", f"{service_name}.service"], capture=True)
    run_as(
        entry,
        [platform["podman"], "exec", service_name, "gitlab-runner", "verify"],
        capture=True,
    )
    run(
        ["curl", "--fail", "--silent", "--show-error", instance["gitlab"]["healthUrl"]],
        capture=True,
    )
    network_name = f"runnerctl-verify-{service_name}-{os.getpid()}"
    run_as(entry, [platform["podman"], "network", "create", network_name], capture=True)
    try:
        command = [
            platform["podman"],
            "run",
            "--rm",
            "--pull=missing",
            "--network",
            network_name,
        ]
        dns = instance["network"].get("dns")
        if dns:
            command.extend(["--dns", dns])
        command.extend(
            [
                instance["validation"]["image"],
                "--fail",
                "--silent",
                "--show-error",
                instance["gitlab"]["healthUrl"],
            ]
        )
        run_as(entry, command, capture=True)
    finally:
        run_as(
            entry,
            [platform["podman"], "network", "rm", "--force", network_name],
            capture=True,
            check=False,
        )


def status(instance_name: str, instance: dict[str, Any]) -> None:
    require_root()
    account_name = instance["account"]["user"]
    try:
        entry = pwd.getpwnam(account_name)
    except KeyError:
        print(f"{instance_name}: account missing")
        return
    runtime_dir = f"/run/user/{entry.pw_uid}"
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": entry.pw_dir,
            "XDG_RUNTIME_DIR": runtime_dir,
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_dir}/bus",
        }
    )
    result = subprocess.run(
        [
            "runuser",
            "--user",
            entry.pw_name,
            "--",
            "systemctl",
            "--user",
            "is-active",
            f"{instance['runner']['serviceName']}.service",
        ],
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    state = result.stdout.strip() or "unavailable"
    registered = "registered" if "token" in registration_metadata(
        Path(entry.pw_dir) / "gitlab-runner/config/config.toml"
    ) else "unregistered"
    print(f"{instance_name}: {state}, {registered}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    for command in ("reconcile", "register", "verify", "status"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("instance")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    document = json.loads(args.config.read_text())
    instances = document["instances"]
    platform = document["platform"]
    validate_instances(instances)
    if args.command == "validate":
        print("GitLab Runner configuration is valid")
        return 0

    instance = select_instance(instances, args.instance)
    if args.command == "reconcile":
        reconcile(instance, platform)
    elif args.command == "register":
        register(instance, platform)
    elif args.command == "verify":
        verify(instance, platform)
    elif args.command == "status":
        status(args.instance, instance)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RunnerError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"runnerctl: {error}", file=sys.stderr)
        raise SystemExit(1) from error
