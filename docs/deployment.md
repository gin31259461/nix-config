# Workstation deployment

Run deployment as the Host's selected login user on Arch Linux. The account must
already exist, belong to `wheel`, have native Nix and `yay`, and boot a kernel
whose module directory is present.

## Commands

```bash
# Source validation only.
just check-fast
just check

# Build without activation.
just build

# Routine convergence.
just arch-workstation

# Install/upgrade declared native packages, then converge.
just arch-workstation update

# Complete Nix and adapter diagnostics.
just arch-workstation verbose
just arch-workstation update verbose
```

Routine deployment never installs missing packages. It exits 3 and lists the
missing packages. `update` permits the full pacman upgrade followed by AUR
convergence.

`just arch-workstation` always enables Nix `--show-trace` and
`--print-build-logs`. `verbose` additionally enables Nix `--verbose` and passes
`--verbose` into the deployment artifact, Arch adapter and Home Manager.

For direct execution with the same diagnostic level:

```bash
nix run --show-trace --print-build-logs --verbose .#arch-workstation -- --verbose
```

An app argument cannot change logging for Nix evaluation that occurred before
the app started, so the Nix flags belong before the flake target and the adapter
flag belongs after `--`.

## Deployment order

The built deployment fixes one Home Manager activation package before runtime.
Execution then follows this order:

1. Validate Arch, login identity, administrator group and native command set.
2. Check installed package state and running-kernel compatibility.
3. Preflight core system settings.
4. Preflight optional native modules.
5. If `--update` is selected, resolve inventories and update pacman/AUR packages.
6. Converge core Arch system settings, files, groups and services.
7. Converge optional modules that reported ready.
8. Activate the exact built Home Manager generation.

Core failures stop immediately. Optional modules may continue only when their
adapter returns the dedicated `not ready` status. A highlighted `SKIP optional
module ...` message records that decision. All other optional-module errors are
fatal.

GitLab Runner reconciliation and registration are not part of this workflow.
See [runners](runners.md).

## Failure and recovery

| Result | Meaning |
| --- | --- |
| Exit 2 | Invalid CLI arguments |
| Exit 3 | Declared native packages are missing; rerun with `update` |
| Exit 75 | Deployment lock is busy or the running kernel no longer matches installed modules |
| Highlighted optional skip | The module is enabled but has not completed explicit preparation |
| Adapter command failure | Inspect the complete command, stdout and stderr and correct the native cause |

Privileged system and AI adapters use the shared native command adapter. Failed
commands include the executable, exit status, stdout and stderr. Timeout errors
also preserve partial output. In verbose mode every native command and its
captured output is printed.

Managed writes compare content and metadata and use atomic replacement. Actions
that must follow a write are recorded under `/var/lib/nix-config/arch/` before
mutation and cleared only after success. Leave pending markers intact after a
failure; the next deployment retries the unfinished action.

A pacman update that replaces the running kernel stops before later convergence
when `/usr/lib/modules/$(uname -r)` is unavailable. Reboot into the installed
kernel and rerun the same deployment command.

The Arch stage and Home Manager stage do not share a rollback transaction. If
Home Manager fails, completed Arch work remains applied; fix the reported home
problem and rerun.

## Preparation dependencies

The AI module requires explicit native/model preparation; see [AI service](ai.md).
The selected hotspot requires a NetworkManager connection with local credentials;
see [hotspot](hotspot.md). Noctalia's first storage activation has a user-session
precondition; see [desktop session](desktop-session.md).

Disabling a capability stops declaring future management. Deployment does not
automatically uninstall packages, delete service state, remove accounts, purge
registrations or erase application data.
