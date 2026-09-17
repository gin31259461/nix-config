import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(sys.argv.pop()).resolve()
spec = importlib.util.spec_from_file_location("searxng_adapter", SOURCE)
assert spec is not None and spec.loader is not None
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class FakeRun:
    def __init__(self):
        self.calls: list[tuple[str, ...]] = []
        self.enabled: set[str] = set()
        self.active: set[str] = set()

    def __call__(self, *argv, allow_failure=False):
        self.calls.append(argv)
        output, code = "", 0
        if argv[:3] == ("systemctl", "is-enabled", "--quiet"):
            code = 0 if argv[3] in self.enabled else 1
        elif argv[:3] == ("systemctl", "is-active", "--quiet"):
            code = 0 if argv[3] in self.active else 3
        elif argv[:2] == ("systemctl", "enable"):
            self.enabled.add(argv[2])
        elif argv[:2] in (("systemctl", "start"), ("systemctl", "restart")):
            self.active.add(argv[2])
        elif argv[0].endswith("curl"):
            output = '{"results":[{"title":"SearXNG"}]}\n'
        if code and not allow_failure:
            raise adapter.Conflict(f"synthetic failure: {argv[0]}")
        return subprocess.CompletedProcess(argv, code, output, "")


class SearxngTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for directory in (
            "etc/systemd/system",
            "var/lib/nix-config/arch",
            "bin",
        ):
            (self.root / directory).mkdir(parents=True)
        (self.root / "bin/curl").touch()
        self.desired = {
            "enabled": True,
            "unitPath": "/etc/systemd/system/searxng.service",
            "receipt": "/var/lib/nix-config/arch/searxng.ready",
            "pending": "/var/lib/nix-config/arch/searxng.pending",
            "unit": "[Service]\nExecStart=/nix/store/searxng\n",
            "endpoint": "http://127.0.0.1:8888",
            "curl": str(self.root / "bin/curl"),
        }
        self.fake_run = FakeRun()

    def subject(self):
        return adapter.Searxng(self.desired, self.root, self.fake_run)

    def test_converges_unit_and_service_idempotently(self):
        subject = self.subject()
        subject.converge()
        self.assertIn("searxng.service", self.fake_run.enabled)
        self.assertIn("searxng.service", self.fake_run.active)
        self.assertTrue((self.root / "var/lib/nix-config/arch/searxng.ready").exists())
        self.assertFalse(
            (self.root / "var/lib/nix-config/arch/searxng.pending").exists()
        )
        unit = self.root / "etc/systemd/system/searxng.service"
        before = unit.stat().st_ino
        calls = len(self.fake_run.calls)
        subject.converge()
        self.assertEqual(before, unit.stat().st_ino)
        repeated = self.fake_run.calls[calls:]
        self.assertFalse(
            any(
                call[:2] in (("systemctl", "start"), ("systemctl", "restart"))
                for call in repeated
            )
        )

    def test_foreign_unit_is_rejected_before_replacement(self):
        (self.root / "etc/systemd/system/searxng.service").write_text("foreign\n")
        with self.assertRaises(adapter.Conflict):
            self.subject().converge()

    def test_empty_search_fails_readiness(self):
        original_run = self.fake_run

        def empty_search(*argv, allow_failure=False):
            result = original_run(*argv, allow_failure=allow_failure)
            if argv[0].endswith("curl"):
                return subprocess.CompletedProcess(argv, 0, '{"results":[]}\n', "")
            return result

        subject = self.subject()
        subject.run = empty_search
        with self.assertRaisesRegex(adapter.Conflict, "no readiness results"):
            subject.converge()

    def test_unit_change_reloads_systemd(self):
        (self.root / "etc/systemd/system/searxng.service").write_text(
            "[Service]\nExecStart=/nix/store/old-searxng\n"
        )
        (self.root / "var/lib/nix-config/arch/searxng.ready").touch()

        self.subject().converge()

        self.assertIn(("systemctl", "daemon-reload"), self.fake_run.calls)


if __name__ == "__main__":
    unittest.main()
