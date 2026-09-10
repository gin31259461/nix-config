"""Contract tests for the shared Arch native command adapter."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

SOURCE = Path(sys.argv.pop()).resolve()
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location("arch_native", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NativeTests(unittest.TestCase):
    def result(self, code=0, stdout="", stderr=""):
        return subprocess.CompletedProcess(["command"], code, stdout, stderr)

    @mock.patch.object(module.subprocess, "run")
    def test_failure_contains_both_complete_streams(self, run):
        run.return_value = self.result(7, "stdout line\n", "stderr line\n")
        with self.assertRaises(module.Conflict) as raised:
            module.Native().run("false")
        message = str(raised.exception)
        self.assertIn("exit 7", message)
        self.assertIn("/usr/bin/false", message)
        self.assertIn("stdout:\nstdout line", message)
        self.assertIn("stderr:\nstderr line", message)

    @mock.patch.object(module.subprocess, "run")
    def test_check_false_preserves_completed_process(self, run):
        run.return_value = self.result(9, "out", "err")
        result = module.Native().run("probe", check=False)
        self.assertEqual(result.returncode, 9)
        self.assertEqual(result.stdout, "out")
        self.assertEqual(result.stderr, "err")

    @mock.patch.object(module.subprocess, "run")
    def test_verbose_prints_command_and_complete_streams(self, run):
        run.return_value = self.result(0, "out\n", "err\n")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            module.Native(verbose=True).run("probe", "argument")
        self.assertEqual(stdout.getvalue(), "out\n")
        self.assertIn("+ /usr/bin/probe argument", stderr.getvalue())
        self.assertIn("err\n", stderr.getvalue())

    @mock.patch.object(module.subprocess, "run")
    def test_timeout_contains_partial_output(self, run):
        run.side_effect = subprocess.TimeoutExpired(
            ["/usr/bin/probe"], 3, output="partial out", stderr="partial err"
        )
        with self.assertRaises(module.Conflict) as raised:
            module.Native(timeout=3).run("probe")
        message = str(raised.exception)
        self.assertIn("timed out after 3s", message)
        self.assertIn("partial out", message)
        self.assertIn("partial err", message)


if __name__ == "__main__":
    unittest.main()
