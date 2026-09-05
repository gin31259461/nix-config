"""Pure Runner validation and rendering; no host operations."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import fnmatch
import ipaddress
import json
from pathlib import Path
import re
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
            raise RunnerError(
                f"{instance_name} subordinate UID and GID ranges must match"
            )
        for image_name in ("managerImage", "defaultJobImage"):
            image = runner[image_name]
            if not FIXED_IMAGE_PATTERN.fullmatch(image) or image.endswith(":latest"):
                raise RunnerError(
                    f"{instance_name} {image_name} must be qualified and pinned"
                )
        if not runner["allowedImages"] or not any(
            fnmatch.fnmatchcase(runner["defaultJobImage"], pattern)
            for pattern in runner["allowedImages"]
        ):
            raise RunnerError(
                f"{instance_name} defaultJobImage must match allowedImages"
            )
        validation_image = instance["validation"]["image"]
        if not FIXED_IMAGE_PATTERN.fullmatch(
            validation_image
        ) or validation_image.endswith(":latest"):
            raise RunnerError(
                f"{instance_name} validation image must be qualified and pinned"
            )
        for pattern in [*runner["allowedImages"], *runner["allowedServices"]]:
            if not IMAGE_PATTERN.fullmatch(pattern) or pattern.endswith(":latest"):
                raise RunnerError(
                    f"{instance_name} has an invalid image allowlist pattern"
                )
        if runner["concurrent"] != 1:
            raise RunnerError(
                f"{instance_name} must remain a dedicated concurrent=1 stack"
            )
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
                raise RunnerError(
                    f"{instance_name} dns must be an IP address"
                ) from error
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
Description=GitLab Runner manager for {runner["serviceName"]}
Wants=network-online.target
After=network-online.target podman.socket
Requires=podman.socket

[Service]
Type=simple
Environment=XDG_RUNTIME_DIR={runtime_dir}
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path={runtime_dir}/bus
ExecStartPre=-{podman_path} rm --force {runner["serviceName"]}
ExecStart={podman_path} run \\
  --rm \\
  --name {runner["serviceName"]} \\
  --network host \\
  --security-opt label=disable \\
  --stop-signal SIGQUIT \\
  --volume {config_dir}:/etc/gitlab-runner:rw \\
  --volume {cache_dir}:/cache:rw \\
  --volume {socket}:/run/podman/podman.sock:rw \\
  --env DOCKER_HOST=unix:///run/podman/podman.sock \\
{dns_argument}  {runner["managerImage"]} \\
  run \\
  --user=gitlab-runner \\
  --working-directory=/home/gitlab-runner
ExecStop=-{podman_path} stop --time 30 {runner["serviceName"]}
ExecStopPost=-{podman_path} rm --force {runner["serviceName"]}
Restart=always
RestartSec=5
TimeoutStartSec=120
TimeoutStopSec=45
Delegate=yes

[Install]
WantedBy=default.target
"""
