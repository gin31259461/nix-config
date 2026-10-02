"""Additive UFW convergence; never reset or own other tools' netfilter chains."""

from hotspot import converge_firewall
from nix_adapter.firewall import (
    UfwBackend,
    format_port_range,
    parse_ufw_status,
)


def rule_port(rule):
    return format_port_range(rule["fromPort"], rule.get("toPort"))


# Maintain backwards compatibility for callers/tests importing status
status = parse_ufw_status


class Firewall:
    def __init__(self, system, backend=None):
        self.system = system
        self.files = system.files
        self.desired = system.desired["firewall"]
        self.backend = backend or UfwBackend(
            runner=getattr(system, "native", None)
            or getattr(system, "runner", None)
            or (system if hasattr(system, "run") else None),
            files=getattr(system, "files", None),
            systemd=getattr(system, "systemd", None),
            ready_unit_fn=getattr(system, "ready_unit", None),
        )

    def run(self, *args, **kwargs):
        return self.system.run(*args, **kwargs)

    def snapshot(self):
        return self.backend.snapshot()

    def preflight(self, installed):
        return self.backend.preflight(installed)

    def kernel_rule(self, rule, v6):
        return self.backend.kernel_rule(rule, v6)

    def kernel_policy(self):
        return self.backend.kernel_policy()

    def converge(self):
        def on_action():
            if hasattr(self.system, "actions"):
                self.system.actions += 1

        def service_ready():
            if hasattr(self.system, "service"):
                self.system.service("ufw.service", "firewall")

        self.backend.converge_service_rules(
            rules=self.desired["rules"],
            logging=self.desired["logging"],
            profiles="skip",
            on_action=on_action,
            service_ready_fn=service_ready,
        )
        converge_firewall(self.system)
        self.files.clear("firewall")
