"""UFW convergence with scoped rules and explicit destructive ownership receipts."""

import json
import re

from files import Conflict, assignments
from hotspot import converge_firewall


RECEIPT = "/var/lib/nix-config/arch/system-firewall-rules.json"


def rule_port(rule):
    start, end = rule["fromPort"], rule["toPort"]
    return str(start) if end is None or end == start else f"{start}:{end}"


def rule_families(rule):
    source = rule.get("source")
    if source and ":" in source:
        return (True,)
    if source and "." in source:
        return (False,)
    return (False, True)


def rule_key(rule, v6):
    return (
        rule_port(rule),
        rule["protocol"],
        v6,
        rule.get("interface"),
        rule.get("source"),
    )


def receipt_key(rule):
    return json.dumps(
        {
            "fromPort": rule["fromPort"],
            "interface": rule.get("interface"),
            "owner": rule.get("owner", "nix-config"),
            "protocol": rule["protocol"],
            "source": rule.get("source"),
            "toPort": rule["toPort"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def ufw_rule_args(rule):
    # Preserve the compact native syntax for globally scoped rules. Scoped rules
    # use UFW's explicit from/to form so the rendered policy is reviewable.
    if not rule.get("interface") and not rule.get("source"):
        return ["allow", "in", rule_port(rule) + "/" + rule["protocol"]]
    args = ["allow", "in"]
    if rule.get("interface"):
        args.extend(["on", rule["interface"]])
    if rule.get("source"):
        args.extend(["from", rule["source"]])
    args.extend(["to", "any", "port", rule_port(rule), "proto", rule["protocol"]])
    return args


def _parse_rule_line(line):
    body = line.split("#", 1)[0]
    match = re.fullmatch(
        r"(\d+(?::\d+)?)/(tcp|udp)(?: on ([A-Za-z0-9_.-]+))?\s*(\(v6\))?\s+ALLOW IN\s+(.+?)\s*",
        body,
    )
    if not match:
        return None
    port, protocol, interface, target_v6, source = match.groups()
    source = source.strip()
    source_v6 = source.endswith(" (v6)")
    if source_v6:
        source = source[: -len(" (v6)")].rstrip()
    if source == "Anywhere":
        source = None
    return (port, protocol, bool(target_v6) or source_v6, interface, source)


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
        parsed = _parse_rule_line(line)
        if parsed:
            rules.add(parsed)
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

    def receipts(self):
        text = self.files.read(RECEIPT)
        if not text:
            return set()
        try:
            value = json.loads(text)
        except ValueError:
            raise Conflict("invalid firewall ownership receipt") from None
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise Conflict("invalid firewall ownership receipt")
        return set(value)

    def write_receipts(self, receipts):
        self.files.write(RECEIPT, json.dumps(sorted(receipts), indent=2) + "\n", 0o600)

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
        self.receipts()
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
        scope = []
        if rule.get("interface"):
            scope.extend(["-i", rule["interface"]])
        if rule.get("source"):
            scope.extend(["-s", rule["source"]])
        return (
            self.run(
                "ip6tables" if v6 else "iptables",
                "-w",
                "5",
                "-C",
                "ufw6-user-input" if v6 else "ufw-user-input",
                "-p",
                rule["protocol"],
                *scope,
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

    @staticmethod
    def present_rules(rules):
        return [rule for rule in rules if rule.get("state", "present") == "present"]

    def converge(self):
        f, d = self.files, self.desired
        state = self.snapshot()
        receipts = self.receipts()
        pending = f.pending("firewall")

        # Matching operator rules can satisfy a declaration, but only a rule this
        # adapter actually created receives a receipt and may later be retired.
        for rule in d["rules"]:
            keys = {rule_key(rule, v6) for v6 in rule_families(rule)}
            receipt = receipt_key(rule)
            if rule.get("state", "present") == "absent":
                if receipt in receipts:
                    f.mark("firewall")
                    self.run("ufw", "--force", "delete", *ufw_rule_args(rule))
                    self.system.actions += 1
                    receipts.remove(receipt)
                    self.write_receipts(receipts)
                    state = self.snapshot()
                continue
            if not keys <= state["rules"]:
                f.mark("firewall")
                self.run("ufw", *ufw_rule_args(rule))
                self.system.actions += 1
                receipts.add(receipt)
                self.write_receipts(receipts)
                state = self.snapshot()

        present = self.present_rules(d["rules"])
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
                for rule in present
                for v6 in rule_families(rule)
            )
        ):
            f.mark("firewall")
            self.run("ufw", "reload")
            self.system.actions += 1
        # Unit start may load the rules; never stop another network service.
        self.system.service("ufw.service", "firewall")
        final = self.snapshot()
        expected = {
            rule_key(rule, v6) for rule in present for v6 in rule_families(rule)
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
                for rule in present
                for v6 in rule_families(rule)
            )
        ):
            f.mark("firewall")
            raise Conflict("UFW policy or kernel rules did not converge")
        converge_firewall(self.system)
        f.clear("firewall")
