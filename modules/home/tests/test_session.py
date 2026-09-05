"""Assert systemd relationships on generated units, including repeated keys."""

from pathlib import Path
import sys
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
    def test_secret_service_shell_and_repair_order(self):
        keepass = unit("keepassxc")
        shell = unit("noctalia")
        repair = unit("keepassxc-tray-refresh")
        self.assertIn("noctalia.service", keepass["Before"])
        self.assertIn("org.freedesktop.secrets", keepass["ExecStartPost"][0])
        self.assertIn("exit 1", keepass["ExecStartPost"][0])
        self.assertIn("keepassxc.service", shell["After"])
        self.assertIn("keepassxc-tray-refresh.service", shell["Wants"])
        self.assertTrue(
            {"keepassxc.service", "noctalia.service"}.issubset(repair["After"])
        )
        self.assertIn("StatusNotifierWatcher", repair["ExecStartPre"][0])
        self.assertIn("--no-block restart keepassxc.service", repair["ExecStart"][0])

    def test_tray_consumers_and_degraded_launcher(self):
        for name in (
            "remmina-applet",
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
