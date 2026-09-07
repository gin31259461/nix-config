"""Converge a prepared NetworkManager AP without reading or transporting secrets."""

import ipaddress
import json
import re
import shlex

from files import Conflict


def firewall_rules(desired):
    """Return scoped UFW commands and their corresponding IPv4 kernel rules."""
    address = ipaddress.IPv4Interface(desired["address"])
    iface, uplink = desired["interface"], desired["uplink"]
    subnet, host = str(address.network), str(address.ip)
    rules = [
        (
            ["allow", "in", "on", iface, "proto", "udp", "to", "any", "port", "67"],
            [
                "ufw-user-input",
                "-i",
                iface,
                "-p",
                "udp",
                "--dport",
                "67",
                "-j",
                "ACCEPT",
            ],
        )
    ]
    for protocol in ("udp", "tcp"):
        rules.append(
            (
                [
                    "allow",
                    "in",
                    "on",
                    iface,
                    "proto",
                    protocol,
                    "from",
                    subnet,
                    "to",
                    host,
                    "port",
                    "53",
                ],
                [
                    "ufw-user-input",
                    "-i",
                    iface,
                    "-s",
                    subnet,
                    "-d",
                    host,
                    "-p",
                    protocol,
                    "--dport",
                    "53",
                    "-j",
                    "ACCEPT",
                ],
            )
        )
    rules.append(
        (
            ["route", "allow", "in", "on", iface, "out", "on", uplink, "from", subnet],
            [
                "ufw-user-forward",
                "-i",
                iface,
                "-o",
                uplink,
                "-s",
                subnet,
                "-j",
                "ACCEPT",
            ],
        )
    )
    return rules


def canonical_rule(words):
    """Normalize UFW's show-added syntax; unrelated rule forms remain unowned."""
    words = list(words)
    if words[:1] == ["ufw"]:
        words.pop(0)
    routed = words[:1] == ["route"]
    if routed:
        words.pop(0)
    if words[:1] != ["allow"]:
        return None
    words.pop(0)
    result = {"routed": routed, "from": "0.0.0.0/0", "to": "0.0.0.0/0"}
    try:
        while words:
            key = words.pop(0)
            if key in ("in", "out"):
                if words.pop(0) != "on":
                    return None
                result[key] = words.pop(0)
            elif key in ("from", "to"):
                value = words.pop(0)
                result[key] = str(
                    ipaddress.ip_network(
                        "0.0.0.0/0" if value == "any" else value, strict=False
                    )
                )
            elif key in ("port", "proto"):
                result[key] = words.pop(0)
            elif key == "comment":
                words.pop(0)
            else:
                return None
    except (IndexError, ValueError):
        return None
    return tuple(sorted(result.items()))


def converge_firewall(system):
    desired = system.desired.get("hotspot")
    if desired is None:
        return
    rules = firewall_rules(desired)
    existing = set()
    for line in system.run("ufw", "show", "added").stdout.splitlines():
        try:
            existing.add(canonical_rule(shlex.split(line)))
        except ValueError:
            continue
    for command, _ in rules:
        if canonical_rule(command) not in existing:
            system.files.mark("firewall")
            system.run("ufw", *command)
            system.actions += 1
    if any(
        system.run("iptables", "-w", "5", "-C", *rule, check=False).returncode
        for _, rule in rules
    ):
        system.files.mark("firewall")
        system.run("ufw", "reload")
        system.actions += 1
    if any(
        system.run("iptables", "-w", "5", "-C", *rule, check=False).returncode
        for _, rule in rules
    ):
        raise Conflict("hotspot firewall rules did not converge")


class Hotspot:
    def __init__(self, system):
        self.system = system
        self.desired = system.desired["hotspot"]
        self.uuid = None

    def read(self, field):
        return self.system.run(
            "nmcli",
            "--escape",
            "no",
            "-g",
            field,
            "connection",
            "show",
            "uuid",
            self.uuid,
        ).stdout.strip()

    def properties(self):
        d = self.desired
        return {
            "connection.interface-name": d["interface"],
            "connection.autoconnect": "yes" if d["autoconnect"] else "no",
            "802-11-wireless.ssid": d["ssid"],
            "802-11-wireless.band": d["band"],
            "802-11-wireless.channel": str(d["channel"]),
            "ipv4.method": "shared",
            "ipv4.addresses": d["address"],
            "ipv4.shared-dhcp-range": "",
            "ipv4.shared-dhcp-lease-time": "0",
            "ipv6.method": d["ipv6"],
        }

    def selected(self):
        return (
            self.uuid
            in self.system.run(
                "nmcli", "-g", "UUID", "connection", "show", "--active"
            ).stdout.splitlines()
        )

    def active(self):
        if not self.selected():
            return False
        wireless = self.system.run(
            "iw", "dev", self.desired["interface"], "info"
        ).stdout
        channel = re.search(r"^\s*channel (\d+) ", wireless, re.M)
        ssid = re.search(r"^\s*ssid (.*)$", wireless, re.M)
        if (
            not channel
            or int(channel[1]) != self.desired["channel"]
            or not ssid
            or ssid[1] != self.desired["ssid"]
        ):
            return False
        data = json.loads(
            self.system.run(
                "ip", "-j", "-4", "address", "show", "dev", self.desired["interface"]
            ).stdout
        )
        address = ipaddress.IPv4Interface(self.desired["address"])
        return any(
            a.get("local") == str(address.ip)
            and a.get("prefixlen") == address.network.prefixlen
            for link in data
            for a in link.get("addr_info", [])
        )

    def preflight(self):
        d = self.desired
        try:
            address = ipaddress.IPv4Interface(d["address"])
            if address.network.prefixlen > 30 or address.ip in (
                address.network.network_address,
                address.network.broadcast_address,
            ):
                raise ValueError
        except ValueError:
            raise Conflict(
                "hotspot requires a usable IPv4 host address and subnet"
            ) from None
        if d["interface"] == d["uplink"]:
            raise Conflict("hotspot and uplink interfaces must differ")
        self.system.ready_unit("NetworkManager.service")
        # List only identifiers, then inspect an explicit public-property allowlist.
        lines = self.system.run(
            "nmcli", "--escape", "no", "-t", "-f", "UUID,NAME", "connection", "show"
        ).stdout.splitlines()
        matches = [
            line.split(":", 1)[0]
            for line in lines
            if ":" in line and line.split(":", 1)[1] == d["connection"]
        ]
        if len(matches) != 1 or not re.fullmatch(r"[0-9a-fA-F-]{36}", matches[0]):
            raise Conflict(
                "prepare exactly one named hotspot connection and its credentials in NetworkManager before deployment"
            )
        self.uuid = matches[0]
        if (
            self.read("connection.type") != "802-11-wireless"
            or self.read("802-11-wireless.mode") != "ap"
        ):
            raise Conflict("prepared hotspot must be a Wi-Fi AP connection")
        if self.read("802-11-wireless-security.key-mgmt") not in ("wpa-psk", "sae"):
            raise Conflict("prepared hotspot must use WPA personal security")
        if self.read("connection.interface-name") not in ("", d["interface"]):
            raise Conflict("prepared hotspot belongs to a different interface")
        # Detect missing hardware and other active connections before any writes.
        device_uuid = self.system.run(
            "nmcli", "-g", "GENERAL.CON-UUID", "device", "show", d["interface"]
        ).stdout.strip()
        if device_uuid not in ("", "--", self.uuid):
            raise Conflict("hotspot interface is in use by another connection")
        self.system.run("ip", "link", "show", "dev", d["uplink"])

    def converge(self):
        self.preflight()
        changes = []
        for field, expected in self.properties().items():
            actual = self.read(field)
            if field == "ipv4.shared-dhcp-lease-time":
                actual = actual.split()[0]
            if actual == "--":
                actual = ""
            if actual != expected:
                changes.extend((field, expected))
        pending = self.system.files.pending("hotspot")
        selected = self.selected()
        active = self.active()
        activate = (
            selected
            or self.desired["autoconnect"]
            or (
                pending
                and self.system.files.read(self.system.files.marker("hotspot"))
                == "activate\n"
            )
        )
        if changes:
            self.system.files.mark("hotspot", "activate\n" if activate else "pending\n")
            self.system.run(
                "nmcli", "connection", "modify", "uuid", self.uuid, *changes
            )
            self.system.actions += 1
        if activate and (changes or pending or not active):
            self.system.files.mark("hotspot", "activate\n")
            self.system.run(
                "nmcli",
                "connection",
                "up",
                "uuid",
                self.uuid,
                "ifname",
                self.desired["interface"],
            )
            self.system.actions += 1
            if not self.active():
                raise Conflict(
                    "hotspot activation did not converge; pending action retained"
                )
        self.system.files.clear("hotspot")
