"""Execute deployment entry points with isolated fake stages only."""

from pathlib import Path
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

HOME = Path(sys.argv.pop()).read_text()
DEPLOY = Path(sys.argv.pop()).read_text()


class DeploymentTests(unittest.TestCase):
    def test_order_and_argument_rejection_before_arch(self):
        for status, args in (
            (0, []),
            (3, []),
            (75, ["--update"]),
            (0, ["--verbose"]),
            (0, ["-b", "backup"]),
            (0, ["--flake", "other"]),
            (0, ["--dry-run"]),
        ):
            with (
                self.subTest(status=status, args=args),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                for name, body in (
                    ("arch", f"echo arch >> {root}/calls\nexit {status}"),
                    ("home", f"echo home >> {root}/calls"),
                ):
                    path = root / name
                    path.write_text(f"#!{shutil.which('bash')}\n" + body)
                    path.chmod(0o755)
                script = (
                    f"set -euo pipefail\ndeployment_name=fixture\narch_switch={root}/arch\nhome_switch={root}/home\n"
                    + DEPLOY
                )
                result = subprocess.run(
                    ["bash", "-c", script, "deploy", *args], capture_output=True
                )
                rejected = args and args[0] not in ("--update", "--verbose")
                self.assertEqual(result.returncode, 2 if rejected else status)
                calls = (
                    (root / "calls").read_text().splitlines()
                    if (root / "calls").exists()
                    else []
                )
                self.assertEqual(
                    calls, [] if rejected else ["arch"] if status else ["arch", "home"]
                )

    def test_home_activates_exact_generation_with_profile_managing_driver(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            activation = root / "activate"
            activation.write_text(
                f"#!{shutil.which('bash')}\n"
                + "[[ ! -v HOME_MANAGER_BACKUP_EXT && ! -v SKIP_SANITY_CHECKS ]]\n"
                + f'printf "%s\\n" "$@" > {root}/args\n'
            )
            activation.chmod(0o755)
            script = (
                f"set -euo pipefail\nactivation_package={shlex.quote(directory)}\n"
                + HOME
            )
            result = subprocess.run(
                ["bash", "-c", script, "home", "--verbose"],
                env={
                    **os.environ,
                    "HOME_MANAGER_BACKUP_EXT": "backup",
                    "SKIP_SANITY_CHECKS": "1",
                },
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (root / "args").read_text().splitlines(), ["--driver-version", "0"]
            )
            (root / "args").unlink()
            result = subprocess.run(
                ["bash", "-c", script, "home", "--override-input", "other"],
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / "args").exists())


if __name__ == "__main__":
    unittest.main()
