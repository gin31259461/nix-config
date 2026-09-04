#!/usr/bin/env python3

"""Converge dedicated rootless Podman GitLab Runner instances."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import fnmatch
import grp
import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import urlparse


class RunnerError(RuntimeError):
    pass


FIXED_IMAGE_PATTERN = re.compile(
    r"^[a-z0-9.-]+(?::[0-9]+)?/[a-z0-9._/-]+"
    r"(?:@sha256:[a-f0-9]{64}|:[A-Za-z0-9._-]+)$"
)
IMAGE_PATTERN = re.compile(
    r"^[a-z0-9.*?-]+(?::[0-9*]+)?/[A-Za-z0-9._/*?-]+"
    r"(?:@sha256:[a-f0-9*?]{1,64}|:[A-Za-z0-9._*?-]+)$"
)
MEMORY_PATTERN = re.compile(r"^[1-9][0-9]*(?:[kKmMgGtT](?:[bB])?)?$")


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


def gitlab_hostname(instance: dict[str, Any]) -> str:
    hostname = urlparse(instance["gitlab"]["url"]).hostname
    if hostname is None:
        raise RunnerError("GitLab URL does not contain a hostname")
    return hostname


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
        if account["user"] == "root" or len(account["user"]) > 32:
            raise RunnerError(f"unsafe account name for {instance_name}")
        if not re.fullmatch(r"[A-Za-z0-9_.@-]+", runner["serviceName"]):
            raise RunnerError(f"invalid service name for {instance_name}")
        if account["user"] in users or runner["serviceName"] in service_names:
            raise RunnerError("Runner account and service names must be unique")
        if account["uid"] in uids:
            raise RunnerError("Runner account UIDs must be unique")
        users.add(account["user"])
        service_names.add(runner["serviceName"])
        uids.add(account["uid"])

        if account["home"] != f"/home/{account['user']}":
            raise RunnerError(f"{instance_name} must use its dedicated /home directory")
        gitlab_url = urlparse(gitlab["url"])
        health_url = urlparse(gitlab["healthUrl"])
        if (
            gitlab_url.scheme != "https"
            or not gitlab_url.hostname
            or health_url.scheme != "https"
            or health_url.hostname != gitlab_url.hostname
        ):
            raise RunnerError(
                f"{instance_name} GitLab URLs must use the same HTTPS hostname"
            )
        for range_name in ("subUid", "subGid"):
            id_range = account[range_name]
            if id_range["start"] <= 0 or id_range["count"] < 65536:
                raise RunnerError(
                    f"{instance_name} {range_name} must contain at least 65536 IDs"
                )
            if id_range["start"] + id_range["count"] - 1 > 4_294_967_294:
                raise RunnerError(f"{instance_name} has an invalid {range_name} range")
        if account["subUid"] != account["subGid"]:
            raise RunnerError(f"{instance_name} subordinate UID and GID ranges must match")
        for image_name in ("managerImage", "defaultJobImage"):
            image = runner[image_name]
            if not FIXED_IMAGE_PATTERN.fullmatch(image) or image.endswith(":latest"):
                raise RunnerError(f"{instance_name} {image_name} must be qualified and pinned")
        if not runner["allowedImages"] or not any(
            fnmatch.fnmatchcase(runner["defaultJobImage"], pattern)
            for pattern in runner["allowedImages"]
        ):
            raise RunnerError(
                f"{instance_name} defaultJobImage must match allowedImages"
            )
        validation_image = instance["validation"]["image"]
        if (
            not FIXED_IMAGE_PATTERN.fullmatch(validation_image)
            or validation_image.endswith(":latest")
        ):
            raise RunnerError(f"{instance_name} validation image must be qualified and pinned")
        for pattern in [*runner["allowedImages"], *runner["allowedServices"]]:
            if not IMAGE_PATTERN.fullmatch(pattern) or pattern.endswith(":latest"):
                raise RunnerError(f"{instance_name} has an invalid image allowlist pattern")
        if runner["concurrent"] != 1:
            raise RunnerError(f"{instance_name} must remain a dedicated concurrent=1 stack")
        try:
            cpus = Decimal(runner["cpus"])
        except InvalidOperation as error:
            raise RunnerError(f"{instance_name} cpus must be positive") from error
        if not cpus.is_finite() or cpus <= 0:
            raise RunnerError(f"{instance_name} cpus must be positive")
        if not MEMORY_PATTERN.fullmatch(runner["memory"]):
            raise RunnerError(f"{instance_name} memory must be a positive size")
        if runner["shmSizeBytes"] <= 0:
            raise RunnerError(f"{instance_name} shmSizeBytes must be positive")
        required_interface = network.get("requiredInterface")
        if required_interface is not None and not re.fullmatch(
            r"[A-Za-z0-9_.:-]+", required_interface
        ):
            raise RunnerError(f"{instance_name} has an invalid requiredInterface")
        dns = network.get("dns")
        if dns is not None:
            try:
                ipaddress.ip_address(dns)
            except ValueError as error:
                raise RunnerError(f"{instance_name} dns must be an IP address") from error
        ca_certificate = gitlab.get("caCertificate")
        if ca_certificate is not None and Path(ca_certificate).suffix.lower() not in {
            ".crt",
            ".pem",
        }:
            raise RunnerError(f"{instance_name} CA certificate must use .crt or .pem")

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


def ensure_account(
    instance: dict[str, Any], platform: dict[str, str]
) -> pwd.struct_passwd:
    account = instance["account"]
    try:
        entry = pwd.getpwnam(account["user"])
    except KeyError:
        try:
            owner = pwd.getpwuid(account["uid"])
        except KeyError:
            owner = None
        if owner is not None:
            raise RunnerError(
                f"UID {account['uid']} is already owned by {owner.pw_name}"
            )
        run(
            [
                platform["useradd"],
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
        run([platform["usermod"], "--lock", account["user"]])
        entry = pwd.getpwnam(account["user"])

    if entry.pw_uid != account["uid"]:
        raise RunnerError(f"{account['user']} already exists with a different UID")
    if entry.pw_dir != account["home"]:
        raise RunnerError(f"{account['user']} already exists with a different home")
    if grp.getgrgid(entry.pw_gid).gr_name != account["user"]:
        raise RunnerError(f"{account['user']} must use its dedicated primary group")
    supplementary_groups = set(os.getgrouplist(entry.pw_name, entry.pw_gid)) - {
        entry.pw_gid
    }
    if supplementary_groups:
        raise RunnerError(f"{account['user']} must not have supplementary host roles")
    return entry


def atomic_write(
    path: Path,
    content: str,
    *,
    mode: int,
    uid: int,
    gid: int,
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
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as temporary:
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
    registration_count = len(re.findall(r"(?m)^\s*\[\[runners\]\]\s*$", content))
    if registration_count > 1:
        raise RunnerError("dedicated Runner config contains multiple registrations")
    if registration_count == 0:
        return {}
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
    if registration_count == 1 and "token" not in metadata:
        raise RunnerError("dedicated Runner config contains an incomplete registration")
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
    if gitlab.get("caCertificate"):
        certificate = f"/etc/gitlab-runner/certs/{gitlab_hostname(instance)}.crt"
        lines.append(f"  tls-ca-file = {toml_string(certificate)}")
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
Description=GitLab Runner manager for {runner['serviceName']}
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
    platform: dict[str, str],
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    runtime_dir = f"/run/user/{entry.pw_uid}"
    return run(
        [
            platform["runuser"],
            "--user",
            entry.pw_name,
            "--",
            platform["env"],
            "--ignore-environment",
            "PATH=/usr/bin",
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


def remove_managed_file(path: Path) -> bool:
    if not path.exists():
        return False
    path.unlink()
    return True


def wait_for_path(path: Path, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.25)
    raise RunnerError(f"timed out waiting for required runtime path: {path}")


def reconcile_ca(
    instance: dict[str, Any],
    entry: pwd.struct_passwd,
    config_dir: Path,
    platform: dict[str, str],
) -> bool:
    hostname = gitlab_hostname(instance)
    service_name = instance["runner"]["serviceName"]
    manager_certificate = config_dir / "certs" / f"{hostname}.crt"
    system_certificate = (
        Path(platform["caAnchorDirectory"]) / f"nix-config-{service_name}.crt"
    )
    registry_certificate = (
        Path(platform["containerCertsDirectory"])
        / hostname
        / f"nix-config-{service_name}.crt"
    )
    source = instance["gitlab"].get("caCertificate")
    changed = False
    system_trust_changed = False
    if source:
        source_path = Path(source)
        if source_path.suffix.lower() not in {".crt", ".pem"} or not source_path.is_file():
            raise RunnerError("GitLab CA certificate must be a readable .crt or .pem file")
        content = source_path.read_text()
        manager_certificate.parent.mkdir(parents=True, exist_ok=True)
        os.chown(manager_certificate.parent, entry.pw_uid, entry.pw_gid)
        os.chmod(manager_certificate.parent, 0o700)
        for directory in (system_certificate.parent, registry_certificate.parent):
            directory.mkdir(parents=True, exist_ok=True)
            os.chown(directory, 0, 0)
            os.chmod(directory, 0o755)
        manager_changed = atomic_write(
            manager_certificate,
            content,
            mode=0o600,
            uid=entry.pw_uid,
            gid=entry.pw_gid,
        )
        system_trust_changed = atomic_write(
            system_certificate,
            content,
            mode=0o644,
            uid=0,
            gid=0,
        )
        registry_changed = atomic_write(
            registry_certificate,
            content,
            mode=0o644,
            uid=0,
            gid=0,
        )
        changed = manager_changed or system_trust_changed or registry_changed
    else:
        manager_changed = remove_managed_file(manager_certificate)
        system_trust_changed = remove_managed_file(system_certificate)
        registry_changed = remove_managed_file(registry_certificate)
        changed = manager_changed or system_trust_changed or registry_changed
    if system_trust_changed:
        run([platform["trust"], "extract-compat"])
    return changed


def verify_rootless_podman(
    entry: pwd.struct_passwd,
    platform: dict[str, str],
) -> None:
    podman_path = platform["podman"]
    version_result = run_as(
        entry, [podman_path, "--version"], platform=platform, capture=True
    )
    version_match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_result.stdout)
    if version_match is None or tuple(map(int, version_match.groups())) < (4, 2, 0):
        raise RunnerError("rootless Podman 4.2.0 or newer is required")
    info_result = run_as(
        entry,
        [podman_path, "info", "--format", "json"],
        platform=platform,
        capture=True,
    )
    info = json.loads(info_result.stdout)
    if not info.get("host", {}).get("security", {}).get("rootless", False):
        raise RunnerError(f"Podman is not rootless for {entry.pw_name}")
    if info.get("host", {}).get("networkBackend") != "netavark":
        raise RunnerError(f"Podman does not use netavark for {entry.pw_name}")


def verify_aardvark(platform: dict[str, str]) -> None:
    result = run([platform["aardvarkDns"], "--version"], capture=True)
    version = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout + result.stderr)
    if version is None or tuple(map(int, version.groups())) <= (1, 10, 0):
        raise RunnerError("aardvark-dns newer than 1.10.0 is required")


def health_command(instance: dict[str, Any], platform: dict[str, str]) -> list[str]:
    command = [
        platform["curl"],
        "--fail",
        "--silent",
        "--show-error",
        "--connect-timeout",
        "10",
        "--max-time",
        "30",
    ]
    ca_certificate = instance["gitlab"].get("caCertificate")
    if ca_certificate:
        command.extend(["--cacert", ca_certificate])
    command.append(instance["gitlab"]["healthUrl"])
    return command


def check_prerequisites(instance: dict[str, Any], platform: dict[str, str]) -> None:
    required_interface_is_up(instance["network"].get("requiredInterface"), platform["ip"])
    executables = [
        platform[key]
        for key in (
            "curl",
            "env",
            "podman",
            "ip",
            "aardvarkDns",
            "useradd",
            "usermod",
            "runuser",
            "loginctl",
            "systemctl",
        )
    ]
    if instance["gitlab"].get("caCertificate"):
        executables.append(platform["trust"])
    for executable in executables:
        if not Path(executable).is_file():
            raise RunnerError(f"required host executable is missing: {executable}")
    if not Path("/sys/fs/cgroup/cgroup.controllers").is_file():
        raise RunnerError("rootless Podman Runner hosts require cgroup v2")
    verify_aardvark(platform)
    run(health_command(instance, platform), capture=True)


def check(instance_name: str, instance: dict[str, Any], platform: dict[str, str]) -> None:
    require_root()
    check_prerequisites(instance, platform)
    print(f"{instance_name}: prerequisites ready")


def reconcile(instance: dict[str, Any], platform: dict[str, str]) -> bool:
    require_root()
    check_prerequisites(instance, platform)

    entry = ensure_account(instance, platform)
    account = instance["account"]
    ensure_subordinate_range(Path("/etc/subuid"), entry.pw_name, account["subUid"])
    ensure_subordinate_range(Path("/etc/subgid"), entry.pw_name, account["subGid"])
    run([platform["loginctl"], "enable-linger", entry.pw_name])
    run([platform["systemctl"], "start", f"user@{entry.pw_uid}.service"])
    wait_for_path(Path(f"/run/user/{entry.pw_uid}/bus"))
    verify_rootless_podman(entry, platform)
    config_dir, _, unit_dir = ensure_directories(entry)
    ca_changed = reconcile_ca(instance, entry, config_dir, platform)
    config_path = config_dir / "config.toml"
    metadata = registration_metadata(config_path)
    template_changed = atomic_write(
        config_dir / "registration-template.toml",
        render_registration_template(instance),
        mode=0o600,
        uid=entry.pw_uid,
        gid=entry.pw_gid,
    )
    config_changed = atomic_write(
        config_path,
        render_config(instance, metadata),
        mode=0o600,
        uid=entry.pw_uid,
        gid=entry.pw_gid,
    )
    service_name = instance["runner"]["serviceName"]
    unit_changed = atomic_write(
        unit_dir / f"{service_name}.service",
        render_service(instance, entry.pw_uid, platform["podman"]),
        mode=0o600,
        uid=entry.pw_uid,
        gid=entry.pw_gid,
    )

    if unit_changed:
        run_as(
            entry,
            [platform["systemctl"], "--user", "daemon-reload"],
            platform=platform,
        )
    run_as(
        entry,
        [platform["systemctl"], "--user", "enable", "--now", "podman.socket"],
        platform=platform,
    )
    image = instance["runner"]["managerImage"]
    image_exists = run_as(
        entry,
        [platform["podman"], "image", "exists", image],
        platform=platform,
        capture=True,
        check=False,
    )
    image_pulled = image_exists.returncode == 1
    if image_pulled:
        run_as(entry, [platform["podman"], "pull", image], platform=platform)
    elif image_exists.returncode != 0:
        raise RunnerError("unable to inspect the Runner manager image")
    service_unit = f"{service_name}.service"
    run_as(
        entry,
        [platform["systemctl"], "--user", "enable", service_unit],
        platform=platform,
    )
    service_active = run_as(
        entry,
        [platform["systemctl"], "--user", "is-active", service_unit],
        platform=platform,
        capture=True,
        check=False,
    )
    if service_active.returncode != 0:
        run_as(
            entry,
            [platform["systemctl"], "--user", "start", service_unit],
            platform=platform,
        )
    elif template_changed or config_changed or unit_changed or ca_changed or image_pulled:
        run_as(
            entry,
            [platform["systemctl"], "--user", "restart", service_unit],
            platform=platform,
        )
    return template_changed or config_changed or unit_changed or ca_changed or image_pulled


def register(instance: dict[str, Any], platform: dict[str, str]) -> None:
    require_root()
    token = os.environ.get("GITLAB_RUNNER_TOKEN", "")
    if not (token.startswith("glrt-") or token.startswith("glrtr-")):
        raise RunnerError("GITLAB_RUNNER_TOKEN must contain a Runner authentication token")
    try:
        entry = pwd.getpwnam(instance["account"]["user"])
    except KeyError as error:
        raise RunnerError("reconcile the Runner instance before registration") from error
    config_path = Path(entry.pw_dir) / "gitlab-runner/config/config.toml"
    metadata = registration_metadata(config_path)
    if "token" in metadata:
        if metadata["token"] != token:
            raise RunnerError("the dedicated stack already contains a different registration")
        reconcile(instance, platform)
        verify(instance, platform)
        return

    service_name = instance["runner"]["serviceName"]
    runtime_dir = f"/run/user/{entry.pw_uid}"
    registration_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": entry.pw_dir,
        "XDG_RUNTIME_DIR": runtime_dir,
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_dir}/bus",
        "CI_SERVER_URL": instance["gitlab"]["url"],
        "CI_SERVER_TOKEN": token,
        "REGISTER_NON_INTERACTIVE": "true",
    }
    command = [
        platform["runuser"],
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
    verify(instance, platform)


def validate_job_network(
    instance: dict[str, Any],
    platform: dict[str, str],
    entry: pwd.struct_passwd,
) -> None:
    service_name = instance["runner"]["serviceName"]
    network_name = f"runnerctl-verify-{service_name}-{os.getpid()}"
    run_as(
        entry,
        [platform["podman"], "network", "create", network_name],
        platform=platform,
        capture=True,
    )
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
        ca_certificate = instance["gitlab"].get("caCertificate")
        if ca_certificate:
            manager_certificate = (
                Path(entry.pw_dir)
                / "gitlab-runner/config/certs"
                / f"{gitlab_hostname(instance)}.crt"
            )
            command.extend(
                ["--volume", f"{manager_certificate}:/tmp/runner-ca.crt:ro,Z"]
            )
        command.extend(
            [
                instance["validation"]["image"],
                "--fail",
                "--silent",
                "--show-error",
                "--connect-timeout",
                "10",
                "--max-time",
                "30",
            ]
        )
        if ca_certificate:
            command.extend(["--cacert", "/tmp/runner-ca.crt"])
        command.append(instance["gitlab"]["healthUrl"])
        run_as(entry, command, platform=platform, capture=True)
    finally:
        run_as(
            entry,
            [platform["podman"], "network", "rm", "--force", network_name],
            platform=platform,
            capture=True,
            check=False,
        )


def verify(instance: dict[str, Any], platform: dict[str, str]) -> None:
    require_root()
    required_interface_is_up(instance["network"].get("requiredInterface"), platform["ip"])
    entry = pwd.getpwnam(instance["account"]["user"])
    verify_rootless_podman(entry, platform)
    verify_aardvark(platform)
    socket_path = Path(f"/run/user/{entry.pw_uid}/podman/podman.sock")
    if not socket_path.exists() or not stat.S_ISSOCK(socket_path.stat().st_mode):
        raise RunnerError(f"rootless Podman socket is unavailable for {entry.pw_name}")
    service_name = instance["runner"]["serviceName"]
    metadata = registration_metadata(
        Path(entry.pw_dir) / "gitlab-runner/config/config.toml"
    )
    if "token" not in metadata:
        raise RunnerError("the dedicated Runner stack is not registered")
    run_as(
        entry,
        [
            platform["systemctl"],
            "--user",
            "is-active",
            f"{service_name}.service",
        ],
        platform=platform,
        capture=True,
    )
    manager_state = run_as(
        entry,
        [
            platform["podman"],
            "inspect",
            "--format",
            "{{.State.Running}} {{.HostConfig.NetworkMode}} {{.HostConfig.Privileged}}",
            service_name,
        ],
        platform=platform,
        capture=True,
    )
    if manager_state.stdout.strip() != "true host false":
        raise RunnerError(
            "Runner manager must be running, unprivileged, and on the host network"
        )
    runner_help = run_as(
        entry,
        [platform["podman"], "exec", service_name, "gitlab-runner", "--help"],
        platform=platform,
        capture=True,
    )
    if re.search(r"(?m)^\s+lint\s+", runner_help.stdout):
        run_as(
            entry,
            [
                platform["podman"],
                "exec",
                service_name,
                "gitlab-runner",
                "lint",
                "--config",
                "/etc/gitlab-runner/config.toml",
            ],
            platform=platform,
            capture=True,
        )
    run_as(
        entry,
        [platform["podman"], "exec", service_name, "gitlab-runner", "verify"],
        platform=platform,
        capture=True,
    )
    run(health_command(instance, platform), capture=True)
    validate_job_network(instance, platform, entry)


def subordinate_range_matches(path: Path, user: str, desired: dict[str, int]) -> bool:
    if not path.exists():
        return False
    expected = f"{user}:{desired['start']}:{desired['count']}"
    return [line.strip() for line in path.read_text().splitlines()].count(expected) == 1


def status(
    instance_name: str,
    instance: dict[str, Any],
    platform: dict[str, str],
) -> None:
    require_root()
    account_name = instance["account"]["user"]
    try:
        entry = pwd.getpwnam(account_name)
    except KeyError:
        print(
            f"{instance_name}: account=missing, subids=missing, socket=missing, "
            "service=unavailable, container=absent, registration=absent"
        )
        return
    runtime_dir = f"/run/user/{entry.pw_uid}"
    environment = {
        "PATH": "/usr/bin",
        "HOME": entry.pw_dir,
        "XDG_RUNTIME_DIR": runtime_dir,
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_dir}/bus",
    }
    result = subprocess.run(
        [
            platform["runuser"],
            "--user",
            entry.pw_name,
            "--",
            platform["systemctl"],
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
    config_path = Path(entry.pw_dir) / "gitlab-runner/config/config.toml"
    try:
        registered = "present" if "token" in registration_metadata(config_path) else "absent"
    except RunnerError:
        registered = "invalid"
    socket_path = Path(f"/run/user/{entry.pw_uid}/podman/podman.sock")
    socket_state = (
        "present"
        if socket_path.exists() and stat.S_ISSOCK(socket_path.stat().st_mode)
        else "missing"
    )
    account = instance["account"]
    subids = (
        "ok"
        if subordinate_range_matches(Path("/etc/subuid"), entry.pw_name, account["subUid"])
        and subordinate_range_matches(Path("/etc/subgid"), entry.pw_name, account["subGid"])
        else "drifted"
    )
    container_result = run_as(
        entry,
        [
            platform["podman"],
            "inspect",
            "--format",
            "{{.State.Running}} {{.HostConfig.NetworkMode}} {{.HostConfig.Privileged}}",
            instance["runner"]["serviceName"],
        ],
        platform=platform,
        capture=True,
        check=False,
    )
    if container_result.returncode != 0:
        container = "absent"
    elif container_result.stdout.strip() == "true host false":
        container = "secure"
    else:
        container = "invalid"
    print(
        f"{instance_name}: account=present, subids={subids}, socket={socket_state}, "
        f"service={state}, container={container}, registration={registered}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    for command in ("check", "reconcile", "register", "verify", "status"):
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
    if args.command == "check":
        check(args.instance, instance, platform)
    elif args.command == "reconcile":
        changed = reconcile(instance, platform)
        print(f"{args.instance}: {'changed' if changed else 'unchanged'}")
    elif args.command == "register":
        register(instance, platform)
    elif args.command == "verify":
        verify(instance, platform)
        print(f"{args.instance}: verified")
    elif args.command == "status":
        status(args.instance, instance, platform)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RunnerError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"runnerctl: {error}", file=sys.stderr)
        raise SystemExit(1) from error
