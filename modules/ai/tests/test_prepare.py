"""Execute the preparation controller against an isolated model directory."""

import hashlib
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(sys.argv.pop()).resolve()


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload = b"pinned model\n"
        self.model = self.root / "models/model.gguf"
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        curl = fake_bin / "curl"
        curl.write_text(
            f"#!{shutil.which('sh')}\n"
            'while [ "$1" != --output ]; do shift; done\n'
            "shift; printf 'pinned model\\n' >\"$1\"\n"
        )
        curl.chmod(0o755)
        text = SOURCE.read_text()
        text = text.replace(
            "((EUID == 0)) || { printf 'run llama-prepare as root (sudo nix run .#llama-prepare)\\n' >&2; exit 1; }",
            "true",
        ).replace(
            "/run/lock/nix-config-llama-prepare.lock", str(self.root / "prepare.lock")
        )
        text = text.replace(
            "mktemp -d /var/tmp/nix-config-llama.XXXXXXXX",
            f"mktemp -d {self.root}/work.XXXXXXXX",
        )
        text = text.replace(
            "[[ -x /usr/bin/c++ && -x /opt/rocm/bin/hipcc && -f /usr/include/vulkan/vulkan.h ]] || {\n"
            "    printf 'native C++, ROCm, or Vulkan development toolchain is missing\\n' >&2; exit 1;\n"
            "  }",
            "true",
        )
        text = text.replace(" -o0 -g0", "")
        digest = hashlib.sha256(self.payload).hexdigest()
        preamble = f"""set -euo pipefail
source_repository=unused
source_revision={"0" * 40}
grammar_threshold=20000
install_prefix={self.root / "opt"}
model_repository=example/model
model_revision={"1" * 40}
model_file=model.gguf
model_path={self.model}
model_sha256={digest}
"""
        self.script = self.root / "prepare"
        self.script.write_text(preamble + text)
        self.env = os.environ | {"PATH": f"{fake_bin}:{os.environ['PATH']}"}

    def invoke(self, mode="--model-only"):
        return subprocess.run(
            ["bash", str(self.script), mode],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )

    def test_installs_and_verified_repeat_is_quiet(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.model.read_bytes(), self.payload)
        self.assertEqual(self.model.stat().st_mode & 0o777, 0o644)
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_refuses_checksum_mismatch_without_overwrite(self):
        self.model.parent.mkdir()
        self.model.write_text("unowned\n")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.model.read_text(), "unowned\n")

    def test_refuses_model_symlink(self):
        target = self.root / "unowned"
        target.write_text("keep\n")
        self.model.parent.mkdir()
        self.model.symlink_to(target)
        self.assertNotEqual(self.invoke().returncode, 0)
        self.assertEqual(target.read_text(), "keep\n")

    def test_failed_download_checksum_never_creates_final_target(self):
        text = self.script.read_text().replace(
            hashlib.sha256(self.payload).hexdigest(), "f" * 64
        )
        self.script.write_text(text)
        self.assertNotEqual(self.invoke().returncode, 0)
        self.assertFalse(self.model.exists())

    def test_existing_owned_revision_selects_current_and_repeats(self):
        revision = self.root / "opt/revisions" / ("0" * 40 + "-20000")
        (revision / "bin").mkdir(parents=True)
        server = revision / "bin/llama-server"
        server.write_text("binary")
        server.chmod(0o755)
        (revision / "nix-config-build").write_text(f"{'0' * 40} 20000\n")
        result = self.invoke("--build-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        current = self.root / "opt/current"
        self.assertEqual(os.readlink(current), f"revisions/{'0' * 40}-20000")
        result = self.invoke("--build-only")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_refuses_symlink_revision_and_contended_lock(self):
        revisions = self.root / "opt/revisions"
        revisions.mkdir(parents=True)
        (revisions / ("0" * 40 + "-20000")).symlink_to(self.root)
        self.assertNotEqual(self.invoke("--build-only").returncode, 0)
        (revisions / ("0" * 40 + "-20000")).unlink()
        lock = open(self.root / "prepare.lock", "w")
        self.addCleanup(lock.close)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.assertEqual(self.invoke().returncode, 75)


if __name__ == "__main__":
    unittest.main()
