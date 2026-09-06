# Operate GitLab Runners

Declare instances in [hosts/arch/gitlab-runners.nix](../hosts/arch/gitlab-runners.nix).
The [Module](../modules/gitlab-runner/interface.nix) derives dedicated accounts,
homes and service names and validates UID, image and subordinate-ID declarations.
Omitting all instances removes the controller and its native requirements from
composition without deleting existing accounts, registrations or containers.

Runner operations are explicit and separate from workstation deployment.
All commands below using `runnerctl` inspect or mutate live state; source
validation uses `nix flake check` instead.

## Prepare an instance

Deploy native requirements through the workstation's explicit update workflow.
Then build the controller and select one exact instance (`frontend` is declared
by the current Host):

```bash
runnerctl_path="$(nix build --no-link --print-out-paths .#runnerctl)"
sudo "$runnerctl_path/bin/runnerctl" status frontend
sudo "$runnerctl_path/bin/runnerctl" check frontend
sudo "$runnerctl_path/bin/runnerctl" reconcile frontend
```

`status` reports state. `check` inspects native prerequisites, required network
interface readiness and GitLab health. `reconcile` converges the dedicated
account, subordinate IDs, runtime, Podman socket, manager image, configuration
and service. It preserves a single existing registration and rejects conflicting
ownership or supplementary host roles.

Each manager can mount only its own rootless Podman socket. Jobs are unprivileged,
use concurrency one and per-job networks, and receive no host socket. Required
interfaces indicate readiness; configure routing separately.

## Register and verify

If registration is absent, create the Runner in GitLab and set tags, protection,
locking and scheduling policy there. Read the authentication token into the
environment rather than embedding it in command arguments:

```bash
read -rsp 'GitLab Runner token: ' GITLAB_RUNNER_TOKEN
export GITLAB_RUNNER_TOKEN
sudo --preserve-env=GITLAB_RUNNER_TOKEN \
  "$runnerctl_path/bin/runnerctl" register frontend
unset GITLAB_RUNNER_TOKEN
```

Registration output is withheld to protect credentials. An existing registration
with a different token is rejected. Verify the registered instance explicitly:

```bash
sudo "$runnerctl_path/bin/runnerctl" verify frontend
```

Verification checks the manager, registration, isolation and a disposable job
network, which is also removed after failure. It is not a source-only test.
Never copy real tokens or registration metadata into expressions, fixtures,
logs, Git or the Nix store.

## Recover and maintain

Mutations share `/run/lock/nix-config-runner.lock` to serialize updates to shared
subordinate-ID files across instances. Keep the lock inode; unrelated
administrative tools are not coordinated by it.

Atomic writes preserve matching files. Instance config directories hold
`.reconcile.pending` for unfinished manager actions and `.trust.pending` for
CA refreshes. Leave these markers and registration state intact when an
operation fails; correct the cause and rerun the same instance operation.

Native commands time out after five minutes by default; registration uses two
minutes and direct status queries use thirty seconds. A timeout can leave
partial work, so do not erase registration data as a recovery shortcut.

Image tags are explicit but not immutable content hashes. The manager uses an
existing local image when available. Change image policy in the Host or owning
Module, validate the source, then reconcile the affected instance explicitly.
No purge or automatic retirement workflow is provided.

## Change the implementation

| Owner | Responsibility |
| --- | --- |
| `interface.nix` | Normalize Host declarations |
| `runner_model.py` | Validate normalized data and render configuration |
| `host_io.py` | Private process, atomic-file and locking primitives |
| `runnerctl.py` | Lifecycle orchestration |
| `tests/` | Independent declarations and isolated fake-runtime tests |

These files live under [modules/gitlab-runner](../modules/gitlab-runner).
Use `nix flake check` for source validation; live status, reconciliation and
registration cannot substitute for those tests.
