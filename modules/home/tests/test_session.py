"""Assert systemd relationships on generated units, including repeated keys."""

from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
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
    def test_keepassxc_waits_for_tray_host_without_restart_coupling(self):
        keepass = unit("keepassxc")
        self.assertIn("noctalia.service", keepass["After"])
        self.assertNotIn("noctalia.service", keepass.get("PartOf", []))
        command = keepass["ExecStartPre"][0]
        script = command.split(" -c '", 1)[1][:-1].replace("$$", "$")
        # Execute the generated wait with fake native commands only. A watcher
        # can answer before its host is ready; neither absence nor false is ready.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            busctl = root / "busctl"
            busctl.write_text(
                f"#!{shutil.which('bash')}\n"
                f'echo call >> "{root}/calls"\n'
                f'count=$(wc -l < "{root}/calls")\n'
                'case "$count" in 1) exit 1;; 2) echo "b false";; '
                '*) echo "b true";; esac\n'
            )
            busctl.chmod(0o755)
            script = script.replace("/usr/bin/busctl", str(busctl)).replace(
                "/usr/bin/sleep 0.1", ":"
            )
            subprocess.run(["bash", "-c", script], check=True, timeout=3)
            self.assertEqual((root / "calls").read_text().splitlines(), ["call"] * 3)
            # Exhausting the bounded wait still permits password-free startup.
            subprocess.run(
                ["bash", "-c", script.replace("SECONDS + 10", "SECONDS")],
                check=True,
                timeout=3,
            )

    def test_launcher_releases_watcher_before_shell_stops(self):
        launcher = unit("vicinae")
        self.assertIn("noctalia.service", launcher["After"])
        self.assertIn("noctalia.service", launcher.get("BindsTo", []))
        self.assertIn("noctalia.service", launcher["PartOf"])
        self.assertIn("vicinae.service", unit("noctalia").get("Wants", []))
        # Restart only the competing watcher, not communication apps or vaults.
        for name in ("vesktop", "keepassxc", "tailscale-systray"):
            self.assertNotIn("noctalia.service", unit(name).get("PartOf", []))

    def test_vesktop_window_backend_is_consistent(self):
        command = unit("vesktop")["ExecStart"][0]
        self.assertIn("--ozone-platform=x11", command)
        self.assertNotIn("--ozone-platform-hint=wayland", command)
        flags = (UNITS / "../../vesktop-flags.conf").read_text()
        self.assertEqual(flags.strip(), "--ozone-platform=x11")

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
