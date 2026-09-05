from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(sys.argv.pop()).read_text()


class DeploymentTests(unittest.TestCase):
    def test_arch_failure_never_activates_home(self):
        for status, args in (
            (0, []),
            (3, []),
            (75, ["--update"]),
            (0, ["-b", "backup"]),
        ):
            with (
                self.subTest(status=status, args=args),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                for name, body in (
                    ("activate", "exit 0"),
                    ("arch", f"exit {status}"),
                    ("home", f"touch {shlex.quote(str(root / 'activated'))}"),
                ):
                    path = root / name
                    path.write_text(f"#!{shutil.which('bash')}\n" + body)
                    path.chmod(0o755)
                script = (
                    "set -euo pipefail\n"
                    + "\n".join(
                        [
                            f"activation_package={shlex.quote(directory)}",
                            "deployment_name=fixture-workstation",
                            f"arch_switch={shlex.quote(str(root / 'arch'))}",
                            f"home_switch={shlex.quote(str(root / 'home'))}",
                        ]
                    )
                    + "\n"
                    + SOURCE
                )
                result = subprocess.run(
                    ["bash", "-c", script, "deployment", *args], capture_output=True
                )
                self.assertEqual(result.returncode, 2 if "-b" in args else status)
                self.assertEqual(
                    (root / "activated").exists(), status == 0 and "-b" not in args
                )


if __name__ == "__main__":
    unittest.main()
