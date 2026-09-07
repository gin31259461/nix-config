"""Additive UFW convergence; never reset or own other tools' netfilter chains."""

import re

from files import Conflict, assignments


def rule_port(rule):
    start, end = rule["fromPort"], rule["toPort"]
    return str(start) if end is None or end == start else f"{start}:{end}"


def status(text):
    if text.strip() == "Status: inactive":
        return {"active": False, "rules": set()}
    if not text.startswith("Status: active\n"):
        raise Conflict("unrecognized UFW status")
    policy = re.search(
        r"^Default: (deny|allow|reject) \(incoming\), (deny|allow|reject) \(outgoing\), (deny|allow|reject|disabled) \(routed\)$",
        text,
        re.M,
    )
    logging = re.search(r"^Logging: (off|on \((low|medium|high|full)\))$", text, re.M)
    profiles = re.search(r"^New profiles: (skip|allow|deny|reject)$", text, re.M)
    if not policy or not logging or not profiles:
        raise Conflict("incomplete UFW status")
    rules = set()
    for line in text.splitlines():
        match = re.fullmatch(
            r"(\d+(?::\d+)?)/(tcp|udp)\s*(\(v6\))?\s+ALLOW IN\s+Anywhere(?: \(v6\))?\s*(?:#.*)?",
            line,
        )
        if match:
            port, protocol, v6 = match.groups()
            rules.add((port, protocol, bool(v6)))
        elif re.search(r"\b(DENY|REJECT|LIMIT)\b", line):
            # Do not silently append an ineffective allow after another owner's deny.
            raise Conflict(
                "UFW has restrictive rules requiring explicit ownership review"
            )
    return {
        "active": True,
        "rules": rules,
        "policy": policy.groups(),
        "logging": logging[2] or "off",
        "profiles": profiles[1],
    }


class Firewall:
    def __init__(self, system):
        self.system = system
        self.files = system.files
        self.desired = system.desired["firewall"]

    def run(self, *args, **kwargs):
        return self.system.run(*args, **kwargs)

    def snapshot(self):
        return status(self.run("ufw", "status", "verbose").stdout)

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
        port = rule_port(rule)
        match = (
            ["-m", "multiport", "--dports", port] if ":" in port else ["--dport", port]
        )
        return (
            self.run(
                "ip6tables" if v6 else "iptables",
                "-w",
                "5",
                "-C",
                "ufw6-user-input" if v6 else "ufw-user-input",
                "-p",
                rule["protocol"],
                *match,
                "-j",
                "ACCEPT",
                check=False,
            ).returncode
            == 0
        )

    def kernel_policy(self):
        for command in ("iptables", "ip6tables"):
            for chain, policy in (
                ("INPUT", "DROP"),
                ("OUTPUT", "ACCEPT"),
                ("FORWARD", "DROP"),
            ):
                result = self.run(command, "-w", "5", "-S", chain, check=False)
                if (
                    result.returncode
                    or f"-P {chain} {policy}" not in result.stdout.splitlines()
                ):
                    return False
        return True

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
        f.clear("firewall")
