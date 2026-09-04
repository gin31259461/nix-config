#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


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

    def test_cli_exposes_the_arch_runner_lifecycle_without_token_arguments(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RUNNERCTL_PATH), "--config", str(CONFIG_PATH), "--help"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )

        for command in ("check", "reconcile", "register", "status", "validate", "verify"):
            self.assertIn(command, result.stdout)
        self.assertNotIn("--token", result.stdout)

    def test_overlapping_subordinate_ids_are_rejected(self) -> None:
        instances = copy.deepcopy(self.instances)
        instances["dotnet"]["account"]["subUid"]["start"] = 165536
        instances["dotnet"]["account"]["subGid"]["start"] = 165536
        with self.assertRaisesRegex(self.runnerctl.RunnerError, "overlapping subUid"):
            self.runnerctl.validate_instances(instances)

    def test_short_subordinate_id_ranges_are_rejected(self) -> None:
        instances = copy.deepcopy(self.instances)
        instances["frontend"]["account"]["subUid"]["count"] = 65535
        with self.assertRaisesRegex(self.runnerctl.RunnerError, "at least 65536"):
            self.runnerctl.validate_instances(instances)

    def test_gitlab_health_url_must_use_the_coordinator_hostname(self) -> None:
        instances = copy.deepcopy(self.instances)
        instances["frontend"]["gitlab"]["healthUrl"] = "https://other.example/health"
        with self.assertRaisesRegex(self.runnerctl.RunnerError, "same HTTPS hostname"):
            self.runnerctl.validate_instances(instances)

    def test_default_job_image_must_match_the_allowlist(self) -> None:
        instances = copy.deepcopy(self.instances)
        instances["frontend"]["runner"]["allowedImages"] = [
            "docker.io/library/python:*"
        ]
        with self.assertRaisesRegex(self.runnerctl.RunnerError, "match allowedImages"):
            self.runnerctl.validate_instances(instances)

    def test_required_interface_is_optional_and_not_vpn_specific(self) -> None:
        instances = copy.deepcopy(self.instances)
        instances["frontend"]["network"]["requiredInterface"] = None
        self.runnerctl.validate_instances(instances)
        self.assertNotIn("vpn", json.dumps(instances).lower())

    def test_registered_config_preserves_registration_metadata(self) -> None:
        instance = self.instances["frontend"]
        test_value = "test-only-value"
        metadata = {
            "id": "42",
            "token": test_value,
            "token_obtained_at": "2026-01-02T03:04:05Z",
        }
        rendered = self.runnerctl.render_config(instance, metadata)
        self.assertIn(f'token = "{test_value}"', rendered)
        self.assertIn("id = 42", rendered)
        self.assertIn("token_obtained_at = 2026-01-02T03:04:05Z", rendered)
        self.assertIn('host = "unix:///run/podman/podman.sock"', rendered)
        self.assertIn("privileged = false", rendered)

    def test_registered_config_uses_the_managed_ca_when_declared(self) -> None:
        instance = copy.deepcopy(self.instances["frontend"])
        instance["gitlab"]["caCertificate"] = "/nix/store/public-runner-ca.crt"

        rendered = self.runnerctl.render_config(instance, {"token": "test-only-value"})

        self.assertIn(
            'tls-ca-file = "/etc/gitlab-runner/certs/gitlab.wke.csie.ncnu.edu.tw.crt"',
            rendered,
        )

    def test_registration_metadata_rejects_multiple_runners(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            config.write_text('[[runners]]\ntoken = "one"\n[[runners]]\ntoken = "two"\n')
            with self.assertRaisesRegex(self.runnerctl.RunnerError, "multiple registrations"):
                self.runnerctl.registration_metadata(config)

    def test_registration_metadata_rejects_incomplete_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            config.write_text('[[runners]]\nname = "incomplete"\n')
            with self.assertRaisesRegex(self.runnerctl.RunnerError, "incomplete"):
                self.runnerctl.registration_metadata(config)

    def test_registration_metadata_ignores_tokens_outside_a_runner_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            config.write_text('token = "orphaned-marker"\n')

            self.assertEqual(self.runnerctl.registration_metadata(config), {})

    def test_reconcile_checks_prerequisites_before_mutating_accounts(self) -> None:
        instance = self.instances["frontend"]
        with (
            mock.patch.object(self.runnerctl, "require_root"),
            mock.patch.object(
                self.runnerctl,
                "check_prerequisites",
                side_effect=self.runnerctl.RunnerError("not ready"),
            ),
            mock.patch.object(self.runnerctl, "ensure_account") as ensure_account,
        ):
            with self.assertRaisesRegex(self.runnerctl.RunnerError, "not ready"):
                self.runnerctl.reconcile(instance, self.document["platform"])

        ensure_account.assert_not_called()

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

    def test_service_account_rejects_supplementary_host_roles(self) -> None:
        instance = self.instances["frontend"]
        entry = self.runnerctl.pwd.struct_passwd(
            (
                instance["account"]["user"],
                "x",
                instance["account"]["uid"],
                1001,
                "",
                instance["account"]["home"],
                "/bin/bash",
            )
        )
        primary_group = self.runnerctl.grp.struct_group(
            (instance["account"]["user"], "x", 1001, [])
        )
        with (
            mock.patch.object(self.runnerctl.pwd, "getpwnam", return_value=entry),
            mock.patch.object(self.runnerctl.grp, "getgrgid", return_value=primary_group),
            mock.patch.object(self.runnerctl.os, "getgrouplist", return_value=[1001, 998]),
        ):
            with self.assertRaisesRegex(self.runnerctl.RunnerError, "supplementary"):
                self.runnerctl.ensure_account(instance, self.document["platform"])

    def test_run_as_clears_the_parent_environment(self) -> None:
        instance = self.instances["frontend"]
        entry = self.runnerctl.pwd.struct_passwd(
            (
                instance["account"]["user"],
                "x",
                instance["account"]["uid"],
                1001,
                "",
                instance["account"]["home"],
                "/bin/bash",
            )
        )
        completed = subprocess.CompletedProcess([], 0)
        with mock.patch.object(self.runnerctl, "run", return_value=completed) as invoked:
            self.runnerctl.run_as(
                entry,
                [self.document["platform"]["podman"], "info"],
                platform=self.document["platform"],
            )

        arguments = invoked.call_args.args[0]
        self.assertIn("--ignore-environment", arguments)
        self.assertIn("PATH=/usr/bin", arguments)

    def test_atomic_write_preserves_an_unchanged_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "managed"
            path.write_text("desired\n")
            path.chmod(0o600)
            before = path.stat()

            changed = self.runnerctl.atomic_write(
                path,
                "desired\n",
                mode=0o600,
                uid=os.getuid(),
                gid=os.getgid(),
            )

            self.assertFalse(changed)
            self.assertEqual(before.st_ino, path.stat().st_ino)

    def test_atomic_write_removes_a_temporary_file_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "managed"
            with mock.patch.object(
                self.runnerctl.os,
                "replace",
                side_effect=OSError("simulated replacement failure"),
            ):
                with self.assertRaises(OSError):
                    self.runnerctl.atomic_write(
                        path,
                        "sensitive test value\n",
                        mode=0o600,
                        uid=os.getuid(),
                        gid=os.getgid(),
                    )

            self.assertEqual(list(root.iterdir()), [])

    def test_registration_passes_only_an_allowlisted_environment(self) -> None:
        instance = self.instances["frontend"]
        authentication_value = "".join(("gl", "rt-", "test-only-value"))
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config_directory = home / "gitlab-runner/config"
            config_directory.mkdir(parents=True)
            entry = self.runnerctl.pwd.struct_passwd(
                (
                    instance["account"]["user"],
                    "x",
                    os.getuid(),
                    os.getgid(),
                    "",
                    str(home),
                    "/bin/bash",
                )
            )
            completed = subprocess.CompletedProcess([], 0)
            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "GITLAB_RUNNER_TOKEN": authentication_value,
                        "UNRELATED_SECRET": "must-not-cross-the-boundary",
                    },
                    clear=True,
                ),
                mock.patch.object(self.runnerctl, "require_root"),
                mock.patch.object(self.runnerctl.pwd, "getpwnam", return_value=entry),
                mock.patch.object(self.runnerctl.subprocess, "run", return_value=completed) as invoked,
                mock.patch.object(self.runnerctl, "reconcile"),
                mock.patch.object(self.runnerctl, "verify"),
            ):
                self.runnerctl.register(instance, self.document["platform"])

            arguments = invoked.call_args.args[0]
            environment = invoked.call_args.kwargs["env"]
            self.assertNotIn(authentication_value, arguments)
            self.assertEqual(environment["CI_SERVER_TOKEN"], authentication_value)
            self.assertNotIn("UNRELATED_SECRET", environment)

    def test_job_network_is_removed_when_validation_fails(self) -> None:
        instance = self.instances["frontend"]
        entry = self.runnerctl.pwd.struct_passwd(
            (
                instance["account"]["user"],
                "x",
                os.getuid(),
                os.getgid(),
                "",
                instance["account"]["home"],
                "/bin/bash",
            )
        )
        completed = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(
            self.runnerctl,
            "run_as",
            side_effect=[completed, self.runnerctl.RunnerError("job failed"), completed],
        ) as invoked:
            with self.assertRaisesRegex(self.runnerctl.RunnerError, "job failed"):
                self.runnerctl.validate_job_network(
                    instance,
                    self.document["platform"],
                    entry,
                )

        cleanup_arguments = invoked.call_args_list[-1].args[1]
        self.assertEqual(cleanup_arguments[1:5], ["network", "rm", "--force", cleanup_arguments[-1]])


if __name__ == "__main__":
    unittest.main()
