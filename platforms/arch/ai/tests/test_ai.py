"""Isolated contract tests for the native llama.cpp adapter."""

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
    def __init__(self, stdout="", returncode=0):
        self.stdout, self.returncode = stdout, returncode


class Native:
    def __init__(self):
        self.calls = []
        self.services = {
            "llama-server.service": {
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
            "etc/llama/server",
            "etc/systemd/system/llama-server.service.d",
            "var/lib/nix-config/arch",
            "var/lib/llama/models",
            "opt/llama/revisions/deadbeef-20000/bin",
        ):
            (self.root / name).mkdir(parents=True)
        (self.root / "opt/llama/revisions/deadbeef-20000/bin/llama-server").write_text(
            "binary"
        )
        (self.root / "opt/llama/revisions/deadbeef-20000/nix-config-build").write_text(
            "deadbeef 20000\n"
        )
        (self.root / "opt/llama/current").symlink_to("revisions/deadbeef-20000")
        (self.root / "var/lib/llama/models/model.gguf").write_text("model")
        self.files = runtime.Files(self.root, (os.getuid(), os.getgid()))
        self.native = Native()
        self.desired = {
            "llama": True,
            "proxy": True,
            "localPort": 11435,
            "httpsPort": 443,
            "source": {
                "installPrefix": "/opt/llama",
                "revision": "deadbeef",
                "grammarRepetitionThreshold": 20000,
            },
            "server": {"host": "127.0.0.1", "port": 11434, "modelsMax": 1},
            "model": {
                "id": "agent",
                "path": "/var/lib/llama/models/model.gguf",
                "device": "ROCm0",
                "contextSize": 98304,
                "fitTarget": 1024,
                "cacheTypeK": "q8_0",
                "cacheTypeV": "q8_0",
                "batchSize": 2048,
                "microBatchSize": 512,
                "parallel": 1,
                "reasoningEffort": "medium",
                "temperature": 1.0,
                "topP": 0.95,
                "topK": 20,
                "minP": 0.0,
                "presencePenalty": 0.0,
                "repetitionPenalty": 1.0,
            },
        }

    def ai(self):
        return runtime.AI(self.desired, self.files, self.native)

    def test_converges_single_model_runtime_and_proxy(self):
        self.ai().converge()
        preset = (self.root / "etc/llama/server/models.ini").read_text()
        self.assertIn("[agent]", preset)
        self.assertIn("ctx-size = 98304", preset)
        dropin = (
            self.root / "etc/systemd/system/llama-server.service.d/60-nix-config.conf"
        ).read_text()
        self.assertIn("/opt/llama/current/bin/llama-server", dropin)
        self.assertIn(
            "LD_LIBRARY_PATH=/opt/llama/current/lib:/opt/llama/current/lib64",
            dropin,
        )
        self.assertIn("--reasoning-effort medium", dropin)
        self.assertIn(
            '--chat-template-kwargs {\\"reasoning_effort\\":\\"medium\\"}', dropin
        )
        self.assertTrue(any(c[:2] == ("caddy", "reload") for c in self.native.calls))
        self.assertFalse(any((self.root / "var/lib/nix-config/arch").iterdir()))

    def test_repeat_repairs_no_files_and_performs_no_reload(self):
        self.ai().converge()
        self.native.calls.clear()
        result = self.ai()
        result.converge()
        self.assertEqual(result.updates, 0)
        self.assertFalse(any(c[:2] == ("caddy", "reload") for c in self.native.calls))

    def test_disabled_preserves_state(self):
        path = self.root / "etc/llama/server/models.ini"
        path.write_text("existing")
        marker = self.root / "var/lib/nix-config/arch/system-ai-llama.pending"
        marker.write_text("")
        self.desired = {"llama": False}
        self.ai().converge()
        self.assertEqual(path.read_text(), "existing")
        self.assertTrue(marker.exists())
        self.assertEqual(self.native.calls, [])

    def test_missing_prepared_assets_skip_without_mutation(self):
        (self.root / "opt/llama/current/bin/llama-server").unlink()
        result = self.ai()
        result.converge()
        self.assertEqual(result.updates, 0)
        self.assertEqual(self.native.calls, [])

    def test_pending_restarts_then_clears(self):
        self.files.mark("ai-llama")
        self.ai().converge()
        self.assertIn(
            ("systemctl", "restart", "llama-server.service"), self.native.calls
        )
        self.assertFalse(self.files.pending("ai-llama"))
        self.assertIn(("systemctl", "daemon-reload"), self.native.calls)

    def test_rejects_legacy_runtime_files_before_writes(self):
        legacy = self.root / "etc/systemd/system/llama-server.service.d/60-local.conf"
        legacy.write_text("manual\n")
        with self.assertRaises(runtime.Conflict):
            self.ai().preflight()
        legacy.unlink()
        (self.root / "etc/caddy/conf.d/nix-config-ollama.caddy").write_text("legacy\n")
        with self.assertRaises(runtime.Conflict):
            self.ai().preflight()
        self.assertFalse((self.root / "etc/llama/server/models.ini").exists())

    def test_rejects_mismatched_prepared_receipt(self):
        (self.root / "opt/llama/current/nix-config-build").write_text("other 20000\n")
        with self.assertRaises(runtime.Conflict):
            self.ai().preflight(installed=True)

    def test_rejects_unowned_prepared_selector(self):
        (self.root / "opt/llama/current").unlink()
        (self.root / "opt/llama/current").symlink_to("revisions/other-20000")
        with self.assertRaises(runtime.Conflict):
            self.ai().preflight(installed=True)

    def test_rejects_custom_caddy_and_serve_conflicts(self):
        (self.root / "etc/caddy/Caddyfile").write_text("example.com { respond ok }\n")
        with self.assertRaises(runtime.Conflict):
            self.ai().preflight()
        (self.root / "etc/caddy/Caddyfile").unlink()
        self.native.serve = '{"443":"http://127.0.0.1:9000"}'
        with self.assertRaises(runtime.Conflict):
            self.ai().converge()

    def test_adopts_exact_package_caddyfile(self):
        path = self.root / "etc/caddy/Caddyfile"
        path.write_text(runtime.PACKAGE_CADDY)
        self.assertEqual(self.ai().caddy_main(), runtime.CADDY_MAIN)


if __name__ == "__main__":
    unittest.main()
