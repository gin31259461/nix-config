# GitLab Runners

GitLab Runner instances are declared under `services.gitlabRunner.instances`.
The current Host defines `frontend` and `dotnet`. Each enabled instance owns a
dedicated service account, subordinate UID/GID ranges, rootless Podman runtime,
manager container, service and GitLab registration.

Runner lifecycle is separate from workstation deployment. `just arch-workstation`
installs selected native dependencies when run with `update`, but never creates or
registers Runner instances.

## Prepare

```bash
just prepare-runner frontend
just prepare-runner dotnet
```

Preparation maps to `runnerctl reconcile`. It creates or validates the dedicated
account, subordinate IDs, runtime directories, rootless Podman socket, manager
configuration and user service. Existing resources with conflicting ownership,
UIDs, groups or registration state are rejected rather than replaced.

Before reconciliation, the required network interface declared for the instance
must be available. Current instances require `tailscale0`.

## Initialize registration

Create the Runner in GitLab and obtain its Runner authentication token. Keep the
token in the process environment only for the registration command:

```bash
read -rsp 'GitLab Runner token: ' GITLAB_RUNNER_TOKEN
export GITLAB_RUNNER_TOKEN
just initialize-runner frontend
unset GITLAB_RUNNER_TOKEN
```

`initialize-runner` preserves `GITLAB_RUNNER_TOKEN` through sudo only for the
`runnerctl register` invocation. Do not store tokens in `configuration.nix`, Git,
Nix derivations, command arguments or logs.

An existing registration with a different token is rejected. Registration
requires prior reconciliation.

## Verify and inspect

```bash
just verify-runner frontend
just status-runner frontend

just verify-runner dotnet
just status-runner dotnet
```

Verification checks the dedicated registration, service state, manager image and
mount isolation, rootless Podman socket, GitLab health and a disposable job
network. `status` reports the current account, subordinate IDs, socket, service,
container and registration states without printing registration metadata.

Jobs remain unprivileged, use per-job networks and do not receive the host Podman
socket. Manager access is limited to the instance's own rootless socket.

## Recovery

Runner mutations share `/run/lock/nix-config-runner.lock`. Managed configuration
writes reject symlinks, hard-linked files and unexpected file types. Reconcile
and trust operations retain private pending markers inside the instance config
directory when interrupted.

Correct the reported cause and rerun the same operation. Do not remove
registrations, service accounts, subordinate-ID entries or pending markers merely
to make a retry succeed.

Disabling an instance withdraws its controller and package requirements. It does
not delete the account, container, registration or runtime data.

## Source validation

```bash
just check
nix build --no-link --show-trace --print-build-logs .#runnerctl
```

Runner tests use isolated declarations and fake runtime operations; they do not
register or mutate a live GitLab Runner.
