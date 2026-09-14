import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(sys.argv.pop()).resolve()
spec = importlib.util.spec_from_file_location("personal_agent_adapter", SOURCE)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class FakeRun:
    def __init__(self):
        self.calls = []
        self.group = False
        self.account = False
        self.enabled = False
        self.active = False

    def __call__(self, *argv, allow_failure=False):
        self.calls.append(argv)
        output, code = "", 0
        if argv[:3] == ("getent", "group", "personal-agent"):
            code = 0 if self.group else 2
        elif argv[:3] == ("getent", "passwd", "personal-agent"):
            code = 0 if self.account else 2
            output = (
                "personal-agent:x:900:900::/var/lib/personal-agent:/usr/bin/nologin\n"
                if self.account
                else ""
            )
        elif argv[:2] == ("groupadd", "--system"):
            self.group = True
        elif argv[:2] == ("useradd", "--system"):
            self.account = True
        elif argv[:3] == ("id", "-gn", "personal-agent"):
            output = "personal-agent\n"
        elif argv[:2] == ("install", "-d"):
            Path(argv[-1]).mkdir(parents=True, exist_ok=True)
        elif argv[:3] == ("systemctl", "is-enabled", "--quiet"):
            code = 0 if self.enabled else 1
        elif argv[:3] == ("systemctl", "is-active", "--quiet"):
            code = 0 if self.active else 3
        elif argv[:2] == ("systemctl", "enable"):
            self.enabled = True
        elif argv[:2] in (("systemctl", "start"), ("systemctl", "restart")):
            self.active = True
        if code and not allow_failure:
            raise adapter.Conflict(f"synthetic failure: {argv[0]}")
        return subprocess.CompletedProcess(argv, code, output, "")


class PersonalAgentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for directory in (
            "etc/personal-agent",
            "etc/systemd/system",
            "var/lib/nix-config/arch",
            "bin",
        ):
            (self.root / directory).mkdir(parents=True)
        executable = self.root / "bin/personal-agent"
        executable.touch()
        self.desired = {
            "enabled": True,
            "executable": str(executable),
            "config": "/etc/personal-agent/config.toml",
            "secrets": "/etc/personal-agent/agent.env",
            "state": "/var/lib/personal-agent",
            "unitPath": "/etc/systemd/system/personal-agent.service",
            "receipt": "/var/lib/nix-config/arch/personal-agent.ready",
            "pending": "/var/lib/nix-config/arch/personal-agent.pending",
            "unit": "[Service]\nExecStart=/nix/store/personal-agent\n",
        }
        self.run = FakeRun()

    def write_configuration(self):
        config = self.root / "etc/personal-agent/config.toml"
        config.write_text("[fixture]\nvalue = true\n")
        config.chmod(0o640)
        secrets = self.root / "etc/personal-agent/agent.env"
        secrets.write_text(
            "DISCORD_TOKEN=synthetic-discord\nNOTION_TOKEN=synthetic-notion\n"
        )
        secrets.chmod(0o600)

    def subject(self):
        return adapter.PersonalAgent(self.desired, self.root, self.run)

    def test_first_missing_configuration_is_not_ready(self):
        with self.assertRaises(adapter.NotReady):
            self.subject().preflight()

    def test_missing_prepared_configuration_is_drift(self):
        (self.root / "var/lib/nix-config/arch/personal-agent.ready").touch()
        with self.assertRaises(adapter.Conflict):
            self.subject().preflight()

    def test_invalid_secrets_do_not_enter_diagnostics(self):
        self.write_configuration()
        secrets = self.root / "etc/personal-agent/agent.env"
        secrets.write_text("DISCORD_TOKEN=synthetic-private\nUNKNOWN=value\n")
        with self.assertRaises(adapter.Conflict) as raised:
            self.subject().preflight()
        self.assertNotIn("synthetic-private", str(raised.exception))

    def test_converges_account_unit_and_service_idempotently(self):
        self.write_configuration()
        subject = self.subject()
        subject.converge()
        self.assertTrue(self.run.group and self.run.account)
        self.assertTrue(self.run.enabled and self.run.active)
        self.assertTrue(
            (self.root / "var/lib/nix-config/arch/personal-agent.ready").exists()
        )
        self.assertFalse(
            (self.root / "var/lib/nix-config/arch/personal-agent.pending").exists()
        )
        unit = self.root / "etc/systemd/system/personal-agent.service"
        before = unit.stat().st_ino
        calls = len(self.run.calls)
        subject.converge()
        self.assertEqual(before, unit.stat().st_ino)
        repeated = self.run.calls[calls:]
        self.assertFalse(
            any(
                call[:2] in (("systemctl", "start"), ("systemctl", "restart"))
                for call in repeated
            )
        )

    def test_foreign_unit_is_rejected_before_replacement(self):
        self.write_configuration()
        (self.root / "etc/systemd/system/personal-agent.service").write_text(
            "foreign\n"
        )
        with self.assertRaises(adapter.Conflict):
            self.subject().converge()


if __name__ == "__main__":
    unittest.main()
