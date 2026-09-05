# GitLab Runner operations

Declare instances in [hosts/arch/gitlab-runners.nix](../hosts/arch/gitlab-runners.nix).
The [Module interface](../modules/gitlab-runner/interface.nix) derives dedicated
account names, homes and service names, fixes concurrency to one, and validates
UID uniqueness, image policy and subordinate-ID allocations.

The controller is available only when instances are selected. Emptying or
omitting the Host's `gitlabRunners` removes it from composition without retiring
existing state. Runner operations are separate from workstation deployment.

## Prepare one instance

First deploy the native package requirements through the workstation's explicit
update workflow. Build the controller without activating anything:

```bash
runnerctl_path="$(nix build --no-link --print-out-paths .#runnerctl)"
```

The following commands inspect or modify live state. Choose one exact instance;
`frontend` is an example from the current Host:

```bash
sudo "$runnerctl_path/bin/runnerctl" status frontend
sudo "$runnerctl_path/bin/runnerctl" check frontend
sudo "$runnerctl_path/bin/runnerctl" reconcile frontend
```

`check` verifies native prerequisites, the required network interface and GitLab
health. `reconcile` converges the account, subordinate IDs, user runtime, Podman
socket, manager image, configuration and service. It preserves an existing
single registration and rejects conflicting account ownership or host roles.

Managers can mount only their own rootless Podman socket. Job configuration has
no host socket, stays unprivileged and uses per-job networks. A
`network.requiredInterface` value is readiness only; configure routing elsewhere.

## Register and verify

When status reports registration absent, create the Runner in GitLab and set
tags, protection, locking and scheduling policy there. Pass the authentication
token through the environment, never a command-line argument:

```bash
read -rsp 'GitLab Runner token: ' GITLAB_RUNNER_TOKEN
export GITLAB_RUNNER_TOKEN
sudo --preserve-env=GITLAB_RUNNER_TOKEN \
  "$runnerctl_path/bin/runnerctl" register frontend
unset GITLAB_RUNNER_TOKEN
```

Registration output is suppressed to avoid exposing authentication material.
The controller rejects an existing registration with a different token.
After registration, or when checking live isolation and connectivity:

```bash
sudo "$runnerctl_path/bin/runnerctl" verify frontend
```

Verification checks the manager, registration, isolation and a disposable job
network; the network is removed when validation fails too. It is not a
source-only test.

## Retry and maintain

Mutating CLI operations share `/run/lock/nix-config-runner.lock` so different
instances cannot race while updating shared subordinate-ID files. Unrelated
administrative tools do not participate in this lock.

Configuration writes are atomic and unchanged files are preserved. A
`.reconcile.pending` marker in the instance's config directory records a manager
action before managed file changes; failed restarts are retried even when the
next invocation finds matching files. A separate `.trust.pending` marker retains
unfinished CA trust refresh work. Do not copy these markers or registration
files into the repository.

Native command execution has a five-minute default timeout; registration uses
two minutes and the direct status query uses thirty seconds. A timeout can leave
an operation partially completed. Correct the cause and rerun the same instance
operation; do not erase registration data to recover.

Container image tags are explicit, but tags are not immutable content hashes.
The manager uses an existing local image when present. Image policy changes
belong in the Module or Host declaration, followed by build/check and explicit
instance reconciliation.

## Develop the Module

- `interface.nix` normalizes Host declarations.
- `runner_model.py` validates normalized data and renders desired configuration.
- `host_io.py` owns private process, atomic-file and lock primitives.
- `runnerctl.py` orchestrates lifecycle operations.
- `tests/` contains independent instance declarations, shared validation cases
  and temporary-filesystem/fake-runtime tests.

Run `nix flake check` for source validation. Never substitute live
`status`, `check`, `reconcile`, `register` or `verify` for those tests. There is
no purge command or automatic retirement workflow.
