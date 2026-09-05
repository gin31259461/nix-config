"""Public operations against temporary homes and fake native/Nix commands."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("sync", sys.argv.pop())
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.repo, self.config, self.state = [
            root / n for n in ("repo", "config", "state")
        ]
        self.target = self.repo / "homes/test/noctalia/config.toml"
        self.target.parent.mkdir(parents=True)
        self.target.write_text('[theme]\nmode="dark"\n')
        self.config.mkdir()
        self.state.mkdir()
        self.settings = self.state / "settings.toml"
        self.control = root / "control"
        self.commands = []
        self.exported = {"theme": {"mode": "light"}}
        self.fail_build = self.fail_switch = self.running = self.mismatch = False
        self.validation_warning = False
        self.instance = sync.Sync(
            self.repo,
            "test",
            "test@host",
            self.config,
            self.state,
            self.control,
            self.run_fake,
        )
        self.instance.stopped = self.stopped

    def stopped(self):
        sync.require(not self.running, "Exit Noctalia")

    def run_fake(self, argv):
        self.commands.append(argv)
        if argv[0] == "git":
            return str(self.repo).encode() if "rev-parse" in argv else b"tracked"
        if argv[0] == "/usr/bin/noctalia":
            if argv[2] == "validate":
                sync.parse(Path(argv[3]).read_bytes())
                return b"WARN fixture" if self.validation_warning else b"valid"
            return sync.encode(self.exported)
        if argv[:2] == ["/usr/bin/nix", "build"]:
            sync.require(not self.fail_build, "fake build failure")
            return b""
        if argv[:2] == ["/usr/bin/nix", "run"]:
            sync.require(not self.fail_switch, "fake activation failure")
            self.exported = (
                {}
                if self.mismatch
                else sync.merge(
                    sync.parse(self.target.read_bytes()),
                    sync.parse(sync.read(self.settings)),
                )
            )
            return b""
        raise AssertionError("Unexpected command")

    def test_capture_filters_policy_and_review_sections(self):
        self.exported.update(
            {
                "storage": {"key_file": "/private/key"},
                "calendar": {"accounts": [{"password": "fixture"}]},
                "shell": {"command": "private fixture"},
                "future": {},
            }
        )
        self.instance.capture()
        self.assertEqual(
            sync.parse(self.target.read_bytes()), {"theme": {"mode": "light"}}
        )
        self.assertFalse(
            any(argv[:2] == ["/usr/bin/nix", "run"] for argv in self.commands)
        )

    def test_capture_repeat_is_idempotent(self):
        self.instance.capture()
        before = self.target.stat()
        self.instance.capture()
        self.assertEqual(before.st_mtime_ns, self.target.stat().st_mtime_ns)
        self.assertEqual(before.st_ino, self.target.stat().st_ino)

    def test_dry_runs_never_write_or_build(self):
        before = self.target.read_bytes()
        self.instance.capture(dry_run=True)
        self.instance.deploy(dry_run=True)
        self.assertEqual(before, self.target.read_bytes())
        self.assertFalse(self.control.exists())
        self.assertFalse(any(argv[0] == "/usr/bin/nix" for argv in self.commands))

    def test_conflict_refuses_before_build(self):
        self.settings.write_text('[theme]\nmode="light"\n')
        with self.assertRaisesRegex(RuntimeError, "override conflicts"):
            self.instance.deploy()
        self.assertFalse(self.control.exists())

    def test_replace_preserves_unowned_settings_and_backup(self):
        original = '[theme]\nmode="light"\n[weather]\ncity="fixture"\n'
        self.settings.write_text(original)
        self.instance.deploy(replace=True)
        self.assertEqual(
            sync.parse(self.settings.read_bytes()), {"weather": {"city": "fixture"}}
        )
        backups = list(self.control.glob("settings-*.toml"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), original)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
        self.assertFalse(self.instance.pending.exists())
        self.instance.deploy(replace=True)
        self.assertEqual(len(list(self.control.glob("settings-*.toml"))), 1)

    def test_running_shell_blocks_override_changes(self):
        self.settings.write_text('[theme]\nmode="light"\n')
        original = self.settings.read_bytes()
        self.running = True
        with self.assertRaisesRegex(RuntimeError, "Exit Noctalia"):
            self.instance.deploy(replace=True)
        self.assertEqual(original, self.settings.read_bytes())

    def test_build_failure_does_not_touch_overrides(self):
        self.settings.write_text('[theme]\nmode="light"\n')
        original = self.settings.read_bytes()
        self.fail_build = True
        with self.assertRaisesRegex(RuntimeError, "build failure"):
            self.instance.deploy(replace=True)
        self.assertEqual(original, self.settings.read_bytes())
        self.assertFalse(self.instance.pending.exists())

    def test_activation_failure_restores_override(self):
        self.settings.write_text('[theme]\nmode="light"\n')
        original = self.settings.read_bytes()
        self.fail_switch = True
        with self.assertRaisesRegex(RuntimeError, "activation failure"):
            self.instance.deploy(replace=True)
        self.assertEqual(original, self.settings.read_bytes())
        self.assertFalse(self.instance.pending.exists())

    def test_effective_mismatch_is_failure(self):
        self.mismatch = True
        with self.assertRaisesRegex(RuntimeError, "Effective preferences"):
            self.instance.deploy()

    def test_interrupt_recover_preserves_concurrent_edits(self):
        self.settings.write_text('[theme]\nmode="light"\n')
        original = self.settings.read_bytes()
        run = self.instance.run

        def interrupt(argv):
            if argv[:2] == ["/usr/bin/nix", "run"]:
                raise KeyboardInterrupt()
            return run(argv)

        self.instance.run = interrupt
        with self.assertRaises(KeyboardInterrupt):
            self.instance.deploy(replace=True)
        self.assertTrue(self.instance.pending.exists())
        after = self.settings.read_bytes()
        self.settings.write_text('[theme]\nmode="changed"\n')
        with self.assertRaisesRegex(RuntimeError, "changed after interruption"):
            self.instance.deploy(recover=True)
        self.settings.write_bytes(after)
        self.instance.deploy(recover=True)
        self.assertEqual(original, self.settings.read_bytes())

    def test_symlinks_and_unmanaged_targets_are_rejected(self):
        (self.config / "config.toml").write_text("# unowned")
        with self.assertRaisesRegex(RuntimeError, "Home Manager link"):
            self.instance.deploy()
        self.target.unlink()
        self.target.symlink_to(self.config / "config.toml")
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            self.instance.capture()

    def test_validation_warnings_leave_repository_unchanged(self):
        self.validation_warning = True
        original = self.target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "warnings"):
            self.instance.capture()
        self.assertEqual(original, self.target.read_bytes())

    def test_other_toml_ownership_is_not_overwritten(self):
        (self.config / "theme.toml").write_text('[theme]\nmode="light"\n')
        with self.assertRaisesRegex(RuntimeError, "Another TOML"):
            self.instance.deploy(replace=True)

    def test_receipt_never_contains_override_values(self):
        self.settings.write_text('[theme]\nmode="light"\n')
        run = self.instance.run

        def interrupt(argv):
            if argv[:2] == ["/usr/bin/nix", "run"]:
                raise KeyboardInterrupt()
            return run(argv)

        self.instance.run = interrupt
        with self.assertRaises(KeyboardInterrupt):
            self.instance.deploy(replace=True)
        receipt = json.loads(self.instance.pending.read_text())
        self.assertNotIn("light", json.dumps(receipt))


if __name__ == "__main__":
    unittest.main()
