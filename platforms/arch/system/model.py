"""Static types for the serialized Arch system-settings boundary."""

from typing import Literal, NotRequired, TypedDict


class FirewallRule(TypedDict):
    owner: str
    state: Literal["present", "absent"]
    protocol: Literal["tcp", "udp"]
    fromPort: int
    toPort: int | None
    source: str | None
    interface: str | None


class FirewallConfig(TypedDict):
    provider: Literal["ufw"]
    incoming: Literal["deny"]
    outgoing: Literal["allow"]
    routed: Literal["deny"]
    logging: Literal["off", "low", "medium", "high", "full"]
    rules: list[FirewallRule]


class HostnameConfig(TypedDict):
    enable: bool


class SystemManifest(TypedDict, total=False):
    hostname: str | None
    firewall: FirewallConfig | None
    hotspot: dict[str, object] | None
    locale: dict[str, object] | None
    timeZone: str | None
    console: dict[str, object] | None
    timeSync: dict[str, object] | None
    journal: dict[str, object] | None
    power: dict[str, object] | None
    trim: dict[str, object] | None
    files: dict[str, str]
    # Reserved for forward-compatible manifest members validated by Nix before
    # serialization. Runtime adapters must still opt into each member explicitly.
    _future: NotRequired[None]
