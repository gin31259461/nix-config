"""Privileged file operations exercised only against temporary directories."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, sys.argv.pop())
import host_io as io


class FileTests(unittest.TestCase):
    def test_links_and_special_files_never_touch_external_sentinel(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            sentinel = outside / "file"
            sentinel.write_text("unchanged")
            before = sentinel.stat()
            link = root / "link"
            link.symlink_to(outside, target_is_directory=True)
            for operation in (
                lambda: io.atomic_write(
                    link / "file",
                    "changed",
                    mode=0o600,
                    uid=os.getuid(),
                    gid=os.getgid(),
                ),
                lambda: io.ensure_directory(
                    link, mode=0o700, uid=os.getuid(), gid=os.getgid()
                ),
                lambda: io.read_managed(link / "file"),
                lambda: io.remove_managed_file(link / "file"),
            ):
                with self.assertRaises((OSError, io.RunnerError)):
                    operation()
            for kind in ("symlink", "hardlink", "fifo", "directory"):
                target = root / kind
                if kind == "symlink":
                    target.symlink_to(sentinel)
                elif kind == "hardlink":
                    os.link(sentinel, target)
                elif kind == "fifo":
                    os.mkfifo(target)
                else:
                    target.mkdir()
                with self.assertRaises((OSError, io.RunnerError)):
                    io.atomic_write(
                        target, "changed", mode=0o600, uid=os.getuid(), gid=os.getgid()
                    )
            self.assertEqual(sentinel.read_text(), "unchanged")
            after = sentinel.stat()
            self.assertEqual(
                (before.st_mode, before.st_uid, before.st_gid),
                (after.st_mode, after.st_uid, after.st_gid),
            )

    def test_ancestor_swap_cannot_redirect_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            managed = root / "managed"
            managed.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "file").write_text("sentinel")

            def swap():
                managed.rename(root / "held")
                managed.symlink_to(outside, target_is_directory=True)

            io.atomic_write(
                managed / "file",
                "desired",
                mode=0o600,
                uid=os.getuid(),
                gid=os.getgid(),
                before_change=swap,
            )
            self.assertEqual((outside / "file").read_text(), "sentinel")
            self.assertEqual((root / "held/file").read_text(), "desired")

    def test_write_syncs_file_then_replacement_directory_and_preserves_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "file"
            original = os.fsync
            synced = []

            def sync(fd):
                synced.append(os.fstat(fd).st_mode)
                original(fd)

            with patch.object(io.os, "fsync", side_effect=sync):
                self.assertTrue(
                    io.atomic_write(
                        path, "desired", mode=0o600, uid=os.getuid(), gid=os.getgid()
                    )
                )
            self.assertGreaterEqual(len(synced), 2)
            inode = path.stat().st_ino
            self.assertFalse(
                io.atomic_write(
                    path, "desired", mode=0o600, uid=os.getuid(), gid=os.getgid()
                )
            )
            self.assertEqual(path.stat().st_ino, inode)

    def test_unexpected_owner_is_rejected_before_read_or_metadata_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "file"
            path.write_text("sentinel")
            real = os.fstat

            def wrong_owner(fd):
                values = list(real(fd))
                values[4] = os.geteuid() + 1234
                return os.stat_result(values)

            with patch.object(io.os, "fstat", side_effect=wrong_owner):
                with self.assertRaises(io.RunnerError):
                    io.atomic_write(
                        path, "changed", mode=0o600, uid=os.getuid(), gid=os.getgid()
                    )
                with self.assertRaises(io.RunnerError):
                    io.ensure_directory(
                        Path(directory), mode=0o700, uid=os.getuid(), gid=os.getgid()
                    )
            self.assertEqual(path.read_text(), "sentinel")


if __name__ == "__main__":
    unittest.main()
