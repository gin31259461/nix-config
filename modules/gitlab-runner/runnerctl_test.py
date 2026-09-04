#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


RUNNERCTL_PATH = Path(sys.argv.pop())
CONFIG_PATH = Path(sys.argv.pop())


def load_runnerctl(path: Path):
    spec = importlib.util.spec_from_file_location("runnerctl", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load runnerctl")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RunnerControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runnerctl = load_runnerctl(RUNNERCTL_PATH)
        cls.document = json.loads(CONFIG_PATH.read_text())
        cls.instances = cls.document["instances"]

    def test_host_configuration_is_valid(self) -> None:
        self.runnerctl.validate_instances(self.instances)

    def test_overlapping_subordinate_ids_are_rejected(self) -> None:
        instances = copy.deepcopy(self.instances)
        instances["dotnet"]["account"]["subUid"]["start"] = 165536
        with self.assertRaisesRegex(self.runnerctl.RunnerError, "overlapping subUid"):
            self.runnerctl.validate_instances(instances)

    def test_required_interface_is_optional_and_not_vpn_specific(self) -> None:
        instances = copy.deepcopy(self.instances)
        instances["frontend"]["network"]["requiredInterface"] = None
        self.runnerctl.validate_instances(instances)
        self.assertNotIn("vpn", json.dumps(instances).lower())

    def test_registered_config_preserves_registration_metadata(self) -> None:
        instance = self.instances["frontend"]
        metadata = {
            "id": "42",
            "token": "secret-value",
            "token_obtained_at": "2026-01-02T03:04:05Z",
        }
        rendered = self.runnerctl.render_config(instance, metadata)
        self.assertIn('token = "secret-value"', rendered)
        self.assertIn("id = 42", rendered)
        self.assertIn("token_obtained_at = 2026-01-02T03:04:05Z", rendered)
        self.assertIn('host = "unix:///run/podman/podman.sock"', rendered)
        self.assertIn("privileged = false", rendered)

    def test_registration_metadata_rejects_multiple_runners(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            config.write_text('[[runners]]\ntoken = "one"\n[[runners]]\ntoken = "two"\n')
            with self.assertRaisesRegex(self.runnerctl.RunnerError, "multiple registrations"):
                self.runnerctl.registration_metadata(config)

    def test_manager_mounts_socket_but_job_configuration_does_not(self) -> None:
        instance = self.instances["frontend"]
        manager = self.runnerctl.render_service(
            instance,
            instance["account"]["uid"],
            self.document["platform"]["podman"],
        )
        job = self.runnerctl.render_registration_template(instance)
        self.assertIn("podman.sock:/run/podman/podman.sock:rw", manager)
        self.assertNotIn("podman.sock:/run/podman/podman.sock:rw", job)
        self.assertIn("--network host", manager)
        self.assertIn(
            "  --dns 100.100.100.100 \\\n"
            "  docker.io/gitlab/gitlab-runner:v18.10.1 \\",
            manager,
        )
        self.assertNotIn("\n+", manager)
        self.assertIn('volumes = ["/cache"]', job)


if __name__ == "__main__":
    unittest.main()
