"""Focused orchestration tests for optional modules and verbose adapters."""

import importlib.util
from pathlib import Path
import sys
import unittest

SOURCE = Path(sys.argv.pop()).resolve()
BASE_TEST = Path(__file__).with_name("test_arch_switch.py")
sys.argv.append(str(SOURCE))
spec = importlib.util.spec_from_file_location("arch_switch_base", BASE_TEST)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class OptionalLifecycleTests(unittest.TestCase):
    setUp = base.ArchSwitchTests.setUp
    save = base.ArchSwitchTests.save
    invoke = base.ArchSwitchTests.invoke
    commands = base.ArchSwitchTests.commands

    def test_unprepared_ai_is_skipped_with_high_visibility_warning(self):
        self.state["ai_not_ready"] = True
        self.save()
        result = self.invoke()
        self.assertIn("\x1b[1;33mSKIP optional module ai:", result.stderr)
        ai_calls = [
            call
            for call in self.commands()
            if call[:2] == ["python", "/fixture/ai-adapter"]
        ]
        self.assertEqual(
            ai_calls,
            [["python", "/fixture/ai-adapter", "/fixture/ai-manifest", "preflight"]],
        )
        self.assertIn("Arch converged:", result.stdout)

    def test_verbose_reaches_both_privileged_adapters(self):
        self.invoke("--verbose")
        adapter_calls = [
            call for call in self.commands() if call and call[0] == "python"
        ]
        self.assertTrue(adapter_calls)
        self.assertTrue(all(call[-1] == "--verbose" for call in adapter_calls))


if __name__ == "__main__":
    unittest.main()
