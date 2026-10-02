"""Additive UFW convergence; never reset or own other tools' netfilter chains."""

from hotspot import converge_firewall
from nix_adapter import Conflict, assignments
from nix_adapter.firewall import (
    check_kernel_policy,
    check_kernel_rule,
    format_port_range,
    parse_ufw_status,
)


def rule_port(rule):
    return format_port_range(rule["fromPort"], rule["toPort"])


# Maintain backwards compatibility for callers/tests importing status
status = parse_ufw_status


class Firewall:
    def __init__(self, system):
        self.system = system
        self.files = system.files
        self.desired = system.desired["firewall"]

    def run(self, *args, **kwargs):
        return self.system.run(*args, **kwargs)

    def snapshot(self):
        return parse_ufw_status(self.run("ufw", "status", "verbose").stdout)

    def preflight(self, installed):
        defaults = assignments(self.files.read("/etc/default/ufw"))
        if defaults:
            if defaults.get("IPV6") != "yes" or defaults.get("MANAGE_BUILTINS") != "no":
                raise Conflict(
                    "UFW requires IPv6 and MANAGE_BUILTINS=no to preserve other owners"
                )
            for key, value in [
                ("DEFAULT_INPUT_POLICY", "DROP"),
                ("DEFAULT_OUTPUT_POLICY", "ACCEPT"),
                ("DEFAULT_FORWARD_POLICY", "DROP"),
            ]:
                if defaults.get(key) != value:
                    raise Conflict(
                        "UFW default policy adoption requires operator review"
                    )
        elif installed:
            raise Conflict("UFW defaults are unavailable")
        for name in (
            "ufw.conf",
            "user.rules",
            "user6.rules",
            "before.rules",
            "before6.rules",
            "after.rules",
            "after6.rules",
        ):
            self.files.read("/etc/ufw/" + name)
        state = self.system.unit("nftables.service")
        if state.get("ActiveState") in ("active", "activating") or state.get(
            "UnitFileState"
        ) in ("enabled", "enabled-runtime"):
            raise Conflict("standalone nftables service conflicts with UFW ownership")
        if installed:
            self.system.ready_unit("ufw.service")
            self.snapshot()

    def kernel_rule(self, rule, v6):
        chain = "ufw6-user-input" if v6 else "ufw-user-input"
        port = rule_port(rule)
        return check_kernel_rule(
            chain=chain,
            protocol=rule["protocol"],
            port=port,
            v6=v6,
            runner=self.system.native,
        )

    def kernel_policy(self):
        return check_kernel_policy(runner=self.system.native)

    def converge(self):
        f, d = self.files, self.desired
        state = self.snapshot()
        pending = f.pending("firewall")
        # Existing matching rules are adopted without changing comments or order.
        # Declarations only add requirements; removing one never deletes a rule.
        for rule in d["rules"]:
            expected = {(rule_port(rule), rule["protocol"], v6) for v6 in (False, True)}
            if not expected <= state["rules"]:
                f.mark("firewall")
                self.run("ufw", "allow", "in", rule_port(rule) + "/" + rule["protocol"])
                self.system.actions += 1
        if state.get("logging") != d["logging"]:
            f.mark("firewall")
            self.run("ufw", "logging", d["logging"])
            self.system.actions += 1
        if state.get("profiles") != "skip":
            f.mark("firewall")
            self.run("ufw", "app", "default", "skip")
            self.system.actions += 1
        if not state["active"]:
            f.mark("firewall")
            self.run("ufw", "--force", "enable")
            self.system.actions += 1
        elif (
            pending
            or not self.kernel_policy()
            or any(
                not self.kernel_rule(rule, v6)
                for rule in d["rules"]
                for v6 in (False, True)
            )
        ):
            f.mark("firewall")
            self.run("ufw", "reload")
            self.system.actions += 1
        # Unit start may load the rules; never stop another network service.
        self.system.service("ufw.service", "firewall")
        final = self.snapshot()
        expected = {
            (rule_port(rule), rule["protocol"], v6)
            for rule in d["rules"]
            for v6 in (False, True)
        }
        if (
            not final["active"]
            or not self.kernel_policy()
            or final["policy"] != ("deny", "allow", "deny")
            or final["logging"] != d["logging"]
            or final["profiles"] != "skip"
            or not expected <= final["rules"]
            or any(
                not self.kernel_rule(rule, v6)
                for rule in d["rules"]
                for v6 in (False, True)
            )
        ):
            f.mark("firewall")
            raise Conflict("UFW policy or kernel rules did not converge")
        converge_firewall(self.system)
        f.clear("firewall")
