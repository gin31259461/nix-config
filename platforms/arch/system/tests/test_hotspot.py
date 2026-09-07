"""Prepared AP adoption, public-only changes, and interrupted activation recovery."""

import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from files import Conflict, Files
from hotspot import Hotspot, canonical_rule, firewall_rules
from runtime import System


DESIRED = dict(
    connection="fixture-ap",
    ssid="Fixture",
    interface="wifi0",
    uplink="eth0",
    band="a",
    channel=36,
    address="192.0.2.1/24",
    autoconnect=True,
    ipv6="shared",
)
UUID = "11111111-1111-1111-1111-111111111111"


class Fake:
    def __init__(self):
        self.calls = []
        self.exists = True
        self.duplicate = False
        self.active = True
        self.fail_up = False
        self.channel = 36
        self.device_uuid = UUID
        self.props = Hotspot(
            SimpleNamespace(desired={"hotspot": DESIRED})
        ).properties() | {
            "connection.type": "802-11-wireless",
            "802-11-wireless.mode": "ap",
            "802-11-wireless-security.key-mgmt": "wpa-psk",
        }

    def available(self, command):
        return True

    def run(self, *args, check=True):
        self.calls.append(args)
        if args[0] == "systemctl":
            out = "LoadState=loaded\nActiveState=active\nUnitFileState=enabled"
        elif args[:4] == ("ip", "-j", "-4", "address"):
            out = '[{"addr_info":[{"local":"192.0.2.1","prefixlen":24}]}]'
        elif args[0] == "iw":
            out = f"\tssid Fixture\n\tchannel {self.channel} (5180 MHz)\n"
        elif args[0] == "ip":
            out = ""
        elif "UUID,NAME" in args:
            out = f"{UUID}:fixture-ap\n" * (2 if self.duplicate else int(self.exists))
        elif "GENERAL.CON-UUID" in args:
            out = self.device_uuid
        elif "--active" in args:
            out = UUID if self.active else ""
        elif "-g" in args:
            out = self.props[args[args.index("-g") + 1]]
        elif args[1:3] == ("connection", "modify"):
            self.props.update(zip(args[5::2], args[6::2]))
            out = ""
        elif args[1:3] == ("connection", "up"):
            if self.fail_up:
                self.active = False
                raise Conflict("injected activation failure")
            self.active = True
            self.channel = 36
            out = ""
        else:
            raise AssertionError(args)
        return SimpleNamespace(stdout=out, returncode=0)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.native = Fake()
        self.files = Files(Path(self.temp.name), identity=(os.getuid(), os.getgid()))
        self.system = System({"hotspot": dict(DESIRED)}, self.files, self.native)
        self.ap = Hotspot(self.system)

    def mutations(self):
        return [
            c
            for c in self.native.calls
            if c[1:3] in (("connection", "modify"), ("connection", "up"))
        ]

    def test_adopts_existing_profile_without_mutation_or_secret_access(self):
        self.ap.converge()
        self.assertEqual(self.mutations(), [])
        self.assertFalse(self.files.pending("hotspot"))
        for call in self.native.calls:
            self.assertNotIn("--show-secrets", call)
            self.assertNotIn("802-11-wireless-security.psk", call)

    def test_public_change_and_failed_activation_retry(self):
        self.native.props["802-11-wireless.channel"] = "149"
        self.native.fail_up = True
        with self.assertRaises(Conflict):
            self.ap.converge()
        self.assertTrue(self.files.pending("hotspot"))
        self.native.fail_up = False
        self.ap.converge()
        self.assertFalse(self.files.pending("hotspot"))
        self.assertEqual(sum(c[2] == "modify" for c in self.mutations()), 1)
        count = len(self.mutations())
        self.ap.converge()
        self.assertEqual(len(self.mutations()), count)

    def test_retry_preserves_activation_intent_with_autoconnect_off(self):
        self.system.desired["hotspot"]["autoconnect"] = False
        self.native.fail_up = True
        with self.assertRaises(Conflict):
            self.ap.converge()
        self.assertFalse(self.native.active)
        self.native.fail_up = False
        self.ap.converge()
        self.assertTrue(self.native.active)
        self.assertFalse(self.files.pending("hotspot"))

    def test_disabled_preserves_pending_without_native_calls(self):
        self.files.mark("hotspot", "activate\n")
        self.system.desired["hotspot"] = None
        self.system.converge()
        self.assertTrue(self.files.pending("hotspot"))
        self.assertEqual(self.native.calls, [])

    def test_firewall_disabled_does_not_suppress_hotspot_or_touch_ufw(self):
        self.system.desired["firewall"] = None
        self.native.active = False
        self.system.converge()
        self.assertTrue(self.native.active)
        self.assertFalse(
            any(c[0] in ("ufw", "iptables", "ip6tables") for c in self.native.calls)
        )

    def test_repairs_inactive_profile(self):
        self.native.active = False
        self.native.device_uuid = "--"
        self.ap.converge()
        self.assertEqual(len(self.mutations()), 1)
        self.assertTrue(self.native.active)

    def test_repairs_wireless_runtime_drift_without_rewriting_profile(self):
        self.native.channel = 149
        self.ap.converge()
        self.assertEqual(len(self.mutations()), 1)
        self.assertEqual(self.mutations()[0][2], "up")

    def test_autoconnect_false_does_not_start_or_stop(self):
        self.system.desired["hotspot"]["autoconnect"] = False
        self.native.active = False
        self.native.props["connection.autoconnect"] = "no"
        self.ap.converge()
        self.assertEqual(self.mutations(), [])

    def test_preflight_rejects_missing_duplicate_insecure_and_busy_targets(self):
        for attribute, value in (
            ("exists", False),
            ("duplicate", True),
            ("device_uuid", "another-uuid"),
        ):
            with self.subTest(attribute=attribute):
                previous = getattr(self.native, attribute)
                setattr(self.native, attribute, value)
                with self.assertRaises(Conflict):
                    self.ap.preflight()
                setattr(self.native, attribute, previous)
        self.native.props["802-11-wireless-security.key-mgmt"] = "none"
        with self.assertRaises(Conflict):
            self.ap.preflight()
        self.assertEqual(self.mutations(), [])

    def test_invalid_address_rejected_before_native_calls(self):
        for address in (
            "999.1.1.1/24",
            "192.0.2.0/24",
            "192.0.2.255/24",
            "192.0.2.1/32",
        ):
            self.system.desired["hotspot"]["address"] = address
            with self.assertRaises(Conflict):
                self.ap.preflight()
        self.assertEqual(self.native.calls, [])

    def test_ufw_normalizes_existing_manual_rules(self):
        rules = firewall_rules(DESIRED)
        self.assertEqual(
            canonical_rule(rules[0][0]),
            canonical_rule("ufw allow in on wifi0 to any port 67 proto udp".split()),
        )
        self.assertEqual(
            canonical_rule(rules[1][0]),
            canonical_rule(
                "ufw allow in on wifi0 from 192.0.2.0/24 to 192.0.2.1/32 port 53 proto udp".split()
            ),
        )
        self.assertNotEqual(
            canonical_rule(rules[1][0]),
            canonical_rule(
                "ufw allow in on other from 192.0.2.0/24 to 192.0.2.1 port 53 proto udp".split()
            ),
        )
        self.assertIsNone(canonical_rule("ufw deny 53".split()))


if __name__ == "__main__":
    unittest.main()
