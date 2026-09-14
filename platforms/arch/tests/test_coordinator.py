"""Contract tests for the public Python arch-switch entrypoint."""

import importlib.util
from pathlib import Path
import sys
import unittest

SOURCE = Path(sys.argv.pop()).resolve()
spec = importlib.util.spec_from_file_location("arch_switch_coordinator", SOURCE)
assert spec and spec.loader
coordinator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coordinator)


class CoordinatorTests(unittest.TestCase):
    def test_normalizes_supported_modes(self):
        self.assertEqual(coordinator.normalize([]), [])
        self.assertEqual(coordinator.normalize(["--check"]), ["--check"])
        self.assertEqual(
            coordinator.normalize(["--verbose", "--update"]),
            ["--update", "--verbose"],
        )
        self.assertEqual(
            coordinator.normalize(["--verbose", "--verbose"]), ["--verbose"]
        )

    def test_help_short_circuits_backend_arguments(self):
        self.assertIsNone(coordinator.normalize(["--help"]))
        self.assertIsNone(coordinator.normalize(["--update", "--help"]))

    def test_rejects_unknown_and_conflicting_modes(self):
        with self.assertRaises(ValueError):
            coordinator.normalize(["--unknown"])
        with self.assertRaises(ValueError):
            coordinator.normalize(["--check", "--update"])


if __name__ == "__main__":
    unittest.main()
