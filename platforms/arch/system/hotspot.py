"""Converge a prepared NetworkManager AP without reading or transporting secrets."""

from nix_adapter.firewall import (
    UfwBackend,
    canonical_rule,
    hotspot_firewall_rules,
)
from nix_adapter.hotspot import (
    HotspotManager,
)

__all__ = [
    "Hotspot",
    "canonical_rule",
    "converge_firewall",
    "firewall_rules",
]


def firewall_rules(desired):
    """Return scoped UFW commands and their corresponding IPv4 kernel rules."""
    return hotspot_firewall_rules(
        interface=desired["interface"],
        uplink=desired["uplink"],
        address=desired["address"],
    )


def converge_firewall(system):
    desired = system.desired.get("hotspot")
    if desired is None:
        return
    backend = getattr(system, "firewall_backend", None) or UfwBackend(
        runner=getattr(system, "native", None)
        or getattr(system, "runner", None)
        or (system if hasattr(system, "run") else None),
        files=getattr(system, "files", None),
    )

    def on_action():
        if hasattr(system, "actions"):
            system.actions += 1

    backend.converge_hotspot_rules(
        interface=desired["interface"],
        uplink=desired["uplink"],
        address=desired["address"],
        on_action=on_action,
    )


class Hotspot:
    def __init__(self, system, manager=None):
        self.system = system
        self.desired = system.desired["hotspot"]
        if manager is not None:
            self.manager = manager
        else:
            runner = (
                getattr(system, "native", None)
                or getattr(system, "runner", None)
                or (system if hasattr(system, "run") else None)
            )
            files = getattr(system, "files", None)
            self.manager = HotspotManager(
                desired=self.desired,
                runner=runner,
                files=files,
            )

    @property
    def uuid(self):
        return self.manager.uuid

    @uuid.setter
    def uuid(self, value):
        self.manager.uuid = value

    def read(self, field):
        return self.manager.read_property(field)

    def properties(self):
        return self.manager.properties()

    def selected(self):
        return self.manager.is_selected()

    def active(self):
        return self.manager.is_active()

    def preflight(self):
        ready_unit = getattr(self.system, "ready_unit", None)
        return self.manager.preflight(ready_unit_fn=ready_unit)

    def converge(self):
        def on_action():
            if hasattr(self.system, "actions"):
                self.system.actions += 1

        ready_unit = getattr(self.system, "ready_unit", None)
        self.manager.converge(on_action=on_action, ready_unit_fn=ready_unit)
