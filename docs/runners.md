# GitLab Runner lifecycle

`services.gitlabRunner.instances` declares independent Runner instances. Each enabled instance owns a dedicated service account, subordinate UID/GID range, rootless Podman runtime, manager container, user service and GitLab registration. The Host's current instances and their requirements live in the Runner declarations, not in this runbook.

Runner operations are separate from `just arch-workstation`. The workstation may install declared native dependencies during `update`, but it never reconciles or registers instances. Nix generates each instance's public registration template, non-secret config policy and user service unit. `runnerctl` handles account/runtime checks, registration metadata and token merging at runtime; tokens never enter Git or the Nix store.

## Reconcile an instance

```bash
just prepare-runner frontend
```

Substitute a declared instance name. Reconciliation validates the required active network interface, dedicated account, subordinate ranges and rootless Podman socket, then prepares directories, public configuration, manager image and user service. It rejects conflicts rather than replacing unrelated ownership. It does not create a GitLab registration. Manager access is limited to its own rootless socket; jobs run unprivileged in per-job networks and do not receive that socket.

## Register once

Create a Runner in GitLab and obtain its authentication token. Supply it through the process environment for this command only:

```bash
read -rsp 'GitLab Runner token: ' GITLAB_RUNNER_TOKEN
export GITLAB_RUNNER_TOKEN
just initialize-runner frontend
unset GITLAB_RUNNER_TOKEN
```

Registration requires successful reconciliation and rejects a different existing token. `initialize-runner` preserves the token through sudo only for registration. Never put it in configuration, derivations, command arguments or logs. The command suppresses sensitive registration output.

## Verify, inspect and recover

```bash
just verify-runner frontend
just status-runner frontend
```

Verification checks registration, service, manager image and mount isolation, socket, GitLab health and a disposable job network. Status summarizes state without sensitive metadata. Operations share `/run/lock/nix-config-runner.lock`; managed writes reject symlinks, hard links and unexpected file types. Interrupted reconcile or trust work retains private pending markers inside the instance config directory. Correct the cause and rerun; do not remove registrations, accounts, subordinate-ID entries or markers as a shortcut. Disabling an instance withdraws management and package requirements without deleting runtime state.

Source-only validation:

```bash
just check
nix build --no-link --show-trace --print-build-logs .#runnerctl
```

Tests use isolated declarations and fake operations, not a live GitLab Runner.
