"""Isolated contract tests for the native AI adapter."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(sys.argv.pop()).resolve()
spec = importlib.util.spec_from_file_location("ai_runtime", SOURCE)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class Result:
    def __init__(self, stdout=""):
        self.stdout = stdout
        self.returncode = 0


class Native:
    def __init__(self):
        self.calls = []
        self.services = {
            "ollama.service": {
                "LoadState": "loaded",
                "ActiveState": "inactive",
                "UnitFileState": "disabled",
            },
            "caddy.service": {
                "LoadState": "loaded",
                "ActiveState": "inactive",
                "UnitFileState": "disabled",
            },
        }
        self.serve = "{}"

    def available(self, _):
        return True

    def run(self, *args, check=True):
        self.calls.append(args)
        if args[:2] == ("systemctl", "show"):
            return Result(
                "\n".join(f"{k}={v}" for k, v in self.services[args[2]].items())
            )
        if args[:2] in (
            ("systemctl", "enable"),
            ("systemctl", "start"),
            ("systemctl", "restart"),
        ):
            key = "UnitFileState" if args[1] == "enable" else "ActiveState"
            self.services[args[2]][key] = (
                "enabled" if key == "UnitFileState" else "active"
            )
        if args[:4] == ("tailscale", "serve", "status", "--json"):
            return Result(self.serve)
        if args[:2] == ("stat", "--format=%a:%U:%G"):
            return Result("750:caddy:caddy\n")
        if args[:2] == ("stat", "--format=%F"):
            return Result("socket\n")
        if args[:3] == ("tailscale", "serve", "--bg"):
            self.serve = json.dumps({"443": "http://127.0.0.1:11435"})
        return Result()


class AITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (
            "etc/caddy/conf.d",
            "etc/systemd/system/ollama.service.d",
            "var/lib/nix-config/arch",
        ):
            (self.root / name).mkdir(parents=True)
        self.files = runtime.Files(self.root, (os.getuid(), os.getgid()))
        self.native = Native()
        self.desired = {
            "ollama": True,
            "vulkan": True,
            "proxy": True,
            "keepAlive": -1,
            "visibleDevices": [0],
            "httpsPort": 443,
        }

    def ai(self):
        return runtime.AI(self.desired, self.files, self.native)

    def test_converges_files_services_socket_reload_and_serve(self):
        self.ai().converge()
        self.assertIn(
            "GGML_VK_VISIBLE_DEVICES=0",
            (self.root / "etc/ollama-vulkan.conf").read_text(),
        )
        self.assertIn(
            "SupplementaryGroups=render",
            (
                self.root / "etc/systemd/system/ollama.service.d/60-nix-config.conf"
            ).read_text(),
        )
        self.assertEqual(
            (self.root / "etc/caddy/Caddyfile").read_text(), runtime.CADDY_MAIN
        )
        self.assertTrue(
            any(call[:2] == ("caddy", "reload") for call in self.native.calls)
        )
        self.assertTrue(
            any(
                call[:3] == ("tailscale", "serve", "--bg") for call in self.native.calls
            )
        )
        self.assertFalse(any((self.root / "var/lib/nix-config/arch").iterdir()))

    def test_repeat_is_quiet_and_does_not_reload_or_republish(self):
        self.ai().converge()
        self.native.calls.clear()
        result = self.ai()
        result.converge()
        self.assertEqual(result.updates, 0)
        self.assertFalse(
            any(call[:2] == ("caddy", "reload") for call in self.native.calls)
        )
        self.assertFalse(
            any(
                call[:3] == ("tailscale", "serve", "--bg") for call in self.native.calls
            )
        )

    def test_disabled_preserves_files_pending_and_runtime(self):
        path = self.root / "etc/ollama-vulkan.conf"
        path.write_text("existing\n")
        marker = self.root / "var/lib/nix-config/arch/system-ai-ollama.pending"
        marker.write_text("pending\n")
        self.desired = {"ollama": False}
        self.ai().converge()
        self.assertEqual(path.read_text(), "existing\n")
        self.assertTrue(marker.exists())
        self.assertEqual(self.native.calls, [])

    def test_requires_reviewed_distinct_devices(self):
        for devices in (None, [], [0, 0]):
            self.desired["visibleDevices"] = devices
            with self.assertRaises(runtime.Conflict):
                self.ai().preflight()

    def test_rejects_unowned_ollama_environment(self):
        (self.root / "etc/ollama-vulkan.conf").write_text("PRIVATE_SETTING=value\n")
        with self.assertRaises(runtime.Conflict):
            self.ai().preflight()

    def test_rejects_custom_caddy_and_serve_ownership_conflicts(self):
        (self.root / "etc/caddy/Caddyfile").write_text("example.com { respond ok }\n")
        with self.assertRaises(runtime.Conflict):
            self.ai().preflight()
        (self.root / "etc/caddy/Caddyfile").unlink()
        self.native.serve = '{"443":"http://127.0.0.1:9000"}'
        with self.assertRaises(runtime.Conflict):
            self.ai().converge()

    def test_adopts_only_exact_package_caddyfile(self):
        path = self.root / "etc/caddy/Caddyfile"
        path.write_text(runtime.PACKAGE_CADDY)
        self.assertEqual(self.ai().caddy_main(), runtime.CADDY_MAIN)
        path.write_text(runtime.PACKAGE_CADDY + "example.com { respond ok }\n")
        with self.assertRaises(runtime.Conflict):
            self.ai().preflight()


if __name__ == "__main__":
    unittest.main()
