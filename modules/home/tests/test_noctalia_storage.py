"""Exercise the migration only in temporary directories with fake process state."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("storage", sys.argv.pop())
storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(storage)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.config, self.state, self.cache = [
            root / n for n in ("config", "state", "cache")
        ]
        self.key = root / "data/storage-key/master-key"
        for path in (self.config, self.state, self.cache):
            path.mkdir()
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def prepare(self, apply=True, running=False):
        storage.prepare(
            self.config, self.state, self.cache, self.key, lambda: running, apply
        )

    def test_dry_check_does_not_write(self):
        self.prepare(apply=False)
        self.assertFalse(self.key.parent.exists())

    def test_fresh_key_and_repeat_preserve_content_and_metadata(self):
        self.prepare()
        before = self.key.stat()
        key = self.key.read_bytes()  # Generated fixture, never a real user key.
        self.assertRegex(key, b"^[0-9a-f]{64}$")
        self.assertEqual(before.st_mode & 0o777, 0o600)
        self.assertEqual(self.key.parent.stat().st_mode & 0o777, 0o700)
        (self.config / "storage.toml").write_text('[storage]\nkey_source="file"\n')
        self.prepare(running=True)
        self.assertEqual(key, self.key.read_bytes())
        self.assertEqual(before.st_mtime_ns, self.key.stat().st_mtime_ns)
        self.assertEqual(before.st_ino, self.key.stat().st_ino)

    def test_archive_preserves_old_data(self):
        for source, archive in storage.archives(self.state, self.cache):
            source.mkdir()
            (source / "old.enc").write_bytes(b"fake old encrypted data")
        self.prepare()
        for source, archive in storage.archives(self.state, self.cache):
            self.assertFalse(source.exists())
            self.assertEqual(
                (archive / "old.enc").read_bytes(), b"fake old encrypted data"
            )
        fresh = self.state / "clipboard"
        fresh.mkdir()
        self.prepare()
        self.assertTrue(fresh.exists())

    def test_running_shell_blocks_first_migration_without_writes(self):
        with self.assertRaisesRegex(RuntimeError, "Stop noctalia.service"):
            self.prepare(running=True)
        self.assertFalse(self.key.parent.exists())

    def test_missing_key_is_not_regenerated(self):
        self.prepare()
        self.key.unlink()
        with self.assertRaisesRegex(RuntimeError, "restore it"):
            self.prepare()
        self.assertFalse(self.key.exists())

    def test_conflicting_gui_policy_and_calendar_are_rejected(self):
        for content in (
            '[storage]\nkey_source="secret-service"',
            "[calendar]\nenabled=true",
        ):
            with self.subTest(content=content):
                (self.state / "settings.toml").write_text(content)
                with self.assertRaises(RuntimeError):
                    self.prepare()
                self.assertFalse(self.key.parent.exists())

    def test_archive_collision_and_symlink_are_rejected(self):
        archive = self.state / "clipboard.before-file-key"
        archive.mkdir()
        with self.assertRaisesRegex(RuntimeError, "collision"):
            self.prepare()
        archive.rmdir()
        (self.state / "clipboard").symlink_to(self.cache, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            self.prepare()

    def test_interruption_after_archive_resumes_without_replacement(self):
        old = self.state / "clipboard"
        old.mkdir()
        original_publish = storage.publish

        def fail_key(path, contents):
            if path == self.key:
                raise OSError("simulated interruption")
            original_publish(path, contents)

        with patch.object(storage, "publish", fail_key):
            with self.assertRaises(OSError):
                self.prepare()
        self.assertTrue((self.key.parent / "pending").exists())
        self.assertFalse(old.exists())
        self.prepare()
        self.assertTrue(self.key.exists())
        self.assertFalse((self.key.parent / "pending").exists())

    def test_interruption_after_key_preserves_key(self):
        original_publish = storage.publish

        def fail_ready(path, contents):
            if path.name == "ready":
                raise OSError("simulated interruption")
            original_publish(path, contents)

        with patch.object(storage, "publish", fail_ready):
            with self.assertRaises(OSError):
                self.prepare()
        before = self.key.read_bytes()
        self.prepare()
        self.assertEqual(before, self.key.read_bytes())

    def test_unmanaged_key_and_unsafe_permissions_are_rejected(self):
        self.key.parent.mkdir(parents=True, mode=0o700)
        self.key.write_bytes(b"a" * 64)
        self.key.chmod(0o600)
        with self.assertRaisesRegex(RuntimeError, "Unmanaged"):
            self.prepare()
        self.key.chmod(0o644)
        with self.assertRaisesRegex(RuntimeError, "permissions"):
            self.prepare()

    def test_shell_cannot_run_between_migration_and_config_activation(self):
        self.prepare()
        with self.assertRaisesRegex(RuntimeError, "Finish Noctalia"):
            self.prepare(running=True)

    def test_marker_directory_is_rejected(self):
        self.key.parent.mkdir(parents=True, mode=0o700)
        marker = self.key.parent / "pending"
        marker.mkdir(mode=0o600)
        with self.assertRaisesRegex(RuntimeError, "file type"):
            self.prepare()

    def test_key_directory_collision_has_actionable_error(self):
        self.key.parent.parent.mkdir(parents=True)
        self.key.parent.write_bytes(b"fixture existing key file")
        with self.assertRaisesRegex(
            RuntimeError, "Expected a key directory, found a file; preserve it"
        ):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
