"""Assert systemd relationships on generated units, including repeated keys."""

from pathlib import Path
import sys
import tomllib
import unittest

UNITS = Path(sys.argv.pop())


def unit(name):
    values = {}
    for line in (UNITS / (name + ".service")).read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values.setdefault(key, []).extend(
                value.split()
                if key in {"After", "Before", "Wants", "Requires", "WantedBy", "PartOf"}
                else [value]
            )
    return values


class SessionTests(unittest.TestCase):
    def test_keepassxc_loads_at_login_without_password_delivery(self):
        keepass = unit("keepassxc")
        self.assertEqual(keepass["WantedBy"], ["graphical-session.target"])
        self.assertNotIn("ExecStartPost", keepass)
        self.assertNotIn("LoadCredentialEncrypted", keepass)
        self.assertNotIn("LoadCredential", keepass)
        self.assertEqual(keepass["Restart"], ["no"])
        self.assertEqual(
            keepass["ExecStart"],
            [
                '/usr/bin/keepassxc --minimized "/home/abnertu/.local/share/keepassxc/credentials.kdbx"'
            ],
        )
        self.assertFalse((UNITS / "keepassxc-tray-refresh.service").exists())
        self.assertFalse((UNITS / "remmina-applet.service").exists())
        for path in UNITS.glob("*.service"):
            config = unit(path.stem)
            for key in ("After", "Before", "Wants", "Requires", "BindsTo"):
                self.assertNotIn("keepassxc.service", config.get(key, []), path.name)
            self.assertNotIn("--pw-stdin", path.read_text())
            self.assertNotIn(".cred", path.read_text().replace("credentials.kdbx", ""))
        self.assertTrue(
            (UNITS / "graphical-session.target.wants/keepassxc.service").exists()
        )

    def test_noctalia_uses_a_runtime_file_key(self):
        policy = tomllib.loads((UNITS / "../../noctalia/storage.toml").read_text())
        self.assertEqual(
            policy["storage"],
            {
                "key_source": "file",
                "key_file": "/home/abnertu/.local/share/noctalia/file-key-v1/master-key",
            },
        )
        self.assertFalse(policy["calendar"]["enabled"])
        self.assertFalse(
            (
                UNITS / "../../.." / ".local/share/noctalia/file-key-v1/master-key"
            ).exists()
        )

    def test_tray_consumers_and_degraded_launcher(self):
        for name in (
            "tailscale-systray",
            "vesktop",
            "vicinae",
            "polychromatic-tray",
        ):
            if not (UNITS / (name + ".service")).exists():
                continue
            config = unit(name)
            self.assertIn("noctalia.service", config["After"])
            self.assertIn("noctalia.service", config["Wants"])
            self.assertIn("graphical-session.target", config["PartOf"])
        self.assertTrue(unit("vicinae")["ExecStartPre"][0].endswith("exit 0'"))

    def test_package_units_are_not_copied(self):
        for name in ("app-dev.lizardbyte.app.Sunshine", "sunshine", "openrazer-daemon"):
            self.assertFalse((UNITS / (name + ".service")).exists())
        self.assertTrue(
            (
                UNITS / "app-dev.lizardbyte.app.Sunshine.service.d/override.conf"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()
