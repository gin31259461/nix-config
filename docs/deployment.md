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

# Explicitly remove managed Arch files, units and pending state.
just arch-workstation purge
```

Routine deployment never installs missing packages. It exits with code 3 and lists
the missing packages. Rerunning with `update` permits the full pacman upgrade
followed by declared AUR package convergence.

`purge` is an explicit Arch cleanup. It disables managed system units, removes
managed configuration files and pending state, strips managed settings from
`/etc/nix/nix.conf` (restarting `nix-daemon.service` if active), and removes the
managed repository include. It does not uninstall packages, delete accounts,
unregister Runners, or remove mutable application data. Home Manager state is
intentionally handled by its normal generation lifecycle.

`just arch-workstation` always enables Nix `--show-trace` and
`--print-build-logs`. `verbose` additionally enables Nix `--verbose` and passes
`--verbose` into the deployment artifact, Arch adapter, and Home Manager.

For direct execution with the same diagnostic level:

```bash
nix run --show-trace --print-build-logs --verbose .#arch-workstation -- --verbose
```

Nix evaluation flags belong before the flake target, and adapter flags belong
after `--`.

## Progress display

The operator commands use Nix's native progress bar with build logs while Nix
evaluates and builds their artifacts. After launch, deployment, AI preparation,
and Runner commands use a shared Rich task display. The active task updates on
one line with its name and elapsed time. Completed, skipped, and failed tasks
leave a permanent result line in the terminal history.

During Arch deployment, a filled progress bar tracks the overall remaining
deployment milestones. The completed step count increases as tasks finish,
allowing you to see exactly how many operations remain. Work without a known
total, such as AI preparation or Runner registration, uses a spinner.
Each workflow reports its own tasks; finishing the Arch stage does not mean
Home Manager has finished. Home Manager activation is
announced before handing over to its native output and exit status.

Before commands that print their own logs, progress bars, or input prompts, the
task display yields the terminal to that command. This keeps Nix, pacman/yay,
download tools, compilers, and sudo prompts readable. The task result appears
after the command returns. Detailed command output and error diagnostics retain
their existing handling; progress output is written to stderr.

Redirecting stderr, using `verbose`, setting `TERM=dumb`, or setting `NO_COLOR`
(including an empty value) selects plain task logs without animation or color.
A nonempty `CI` also selects plain task and Nix logs. For example:

```bash
NO_COLOR=1 just build
```

Rich is provided by the Nix-built tools. No separate Python or native package
installation is required for the display. Direct app execution also reports
runtime tasks; the preceding `nix run` build uses Nix's own selected log format.

## Deployment order

The built deployment fixes one Home Manager activation package before runtime.
Execution then follows this order:

1. Validate Arch, login identity, administrator group, and native command set.
2. Check installed package state and running-kernel compatibility.
3. Preflight core system settings.
4. Preflight optional native modules.
5. If `--update` is selected, resolve inventories and update pacman/AUR packages.
6. Converge core Arch system settings, files, groups, services, and `/etc/nix/nix.conf` (managing `trusted-users = root @wheel <user>` while preserving unmanaged lines and restarting `nix-daemon.service` upon change).
7. Converge optional modules that reported ready.
8. Activate the exact built Home Manager generation.

Core failures stop immediately. Optional modules may continue only when their
adapter returns the dedicated `not ready` status. A highlighted `SKIP optional
module ...` message records that decision. All other optional-module errors are
fatal.

GitLab Runner reconciliation and registration are not part of workstation deployment;
see [runners](runners.md). Personal Agent convergence is part of this workflow only
when its external runtime configuration is ready; first-time absence is reported as
an optional skip (see [personal agent](personal-agent.md)).

## Failure and recovery

| Result | Meaning |
| --- | --- |
| Exit 2 | Invalid CLI arguments |
| Exit 3 | Declared native packages are missing; rerun with `update` |
| Exit 75 | Deployment lock is busy or the running kernel no longer matches installed modules |
| Highlighted optional skip | The module is enabled but has not completed explicit preparation |
| Adapter command failure | Inspect the complete command, stdout, and stderr to correct the native cause |

Privileged system and AI adapters use the shared native command adapter. Failed
commands report the executable, exit status, stdout, and stderr. Timeout errors
also preserve partial output. In verbose mode, every native command and its
captured output is printed.

Managed writes compare content and metadata using atomic replacement. Actions
that must follow a write (such as restarting `nix-daemon.service` after
`/etc/nix/nix.conf` changes or `NetworkManager.service` after network changes)
are recorded under `/var/lib/nix-config/arch/` before mutation and cleared only
after success. Leave pending markers intact after a failure; the next deployment
retries the unfinished action.

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
registrations, or erase application data.
