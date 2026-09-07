# Arch system settings

Declare Host values in [hosts/arch/system.nix](../hosts/arch/system.nix).
The [typed interface](../lib/system-settings.nix) validates them; the
[Arch adapter](../platforms/arch/system/default.nix) builds a fixed manifest for
`arch-switch`. Home Manager does not write these system files.

## Initial Host selection

The initial values preserve the system observed on 2026-09-07: English system
messages, generated English and Traditional Chinese UTF-8 locales, Taipei time,
and the Host's `arch` hostname. UFW remains enabled with the existing inbound
rules, IPv4 and IPv6, low logging, incoming/routed deny and outgoing allow.
The exact ports and protocols have one source in
[the Host declaration](../hosts/arch/system.nix).

NTP, journal overrides, console settings, power events and TRIM are initially
unmanaged. Existing NetworkManager, Bluetooth, power-profiles-daemon and Tailscale
service policy remains in [the Arch service inventory](../platforms/arch/services.nix).
Module-owned units, including libvirt and Runner units, retain their owners.

An omitted setting, or `null`, means **leave it unmanaged**. It does not disable
a service, remove a file, remove firewall rules, or restore upstream defaults.
Optional settings have no implicit Host defaults. `hostname.enable` defaults to
false and derives its value from `Host.name` when enabled.

## Adopt and deploy

Build and validate source first using the [deployment workflow](deployment.md).
Before applying it to a host, inspect that exact host's relevant settings and
resolve ownership conflicts. Builds and the isolated VM check do not activate
the real machine. `arch-switch --check` remains an external package inventory
query, not a settings preview.

Routine deployment checks all declared native packages and exits 3 if any are
missing. Only `--update` installs/updates packages. Ownership preflight runs
before configuration writes or package updates, then repeats after updates with
native tool and asset checks. The running-kernel gate still applies.
Arch must succeed before Home Manager activation starts.

Do not pass alternate roots or commands to the system adapter. These seams are
private to source tests. Use the packaged `arch-switch` through the normal
workflow; it holds the deployment lock throughout preflight and convergence.

## Setting contracts

| Setting | Managed scope | When it takes effect |
| --- | --- | --- |
| `locale` | A marked addition to locale.gen and only LANG in locale.conf | Generate first; new language applies to new login sessions |
| `timeZone` | Native localtime symlink through timedatectl | During deployment; RTC mode stays unchanged |
| `hostname.enable` | Static and transient hostname through hostnamectl | During deployment; pretty hostname, hosts file and DNS stay outside scope |
| `timeSync` | A timesyncd drop-in and its service | During deployment; offline systems can still be waiting for synchronization |
| `journal` | A journald drop-in | Restart/flush on change; normal journal rotation enforces retention |
| `console` | Selected KEYMAP/FONT keys in vconsole.conf | Next boot; no live TTY keymap changes |
| `power` | Selected logind power-key/lid-event keys | Next boot; no logind restart or suspend during deployment |
| `firewall` | UFW requirements and missing inbound allow rules | During deployment; other rules stay intact |
| `trim` | Native fstrim.timer with a no-catch-up drop-in | Timer becomes active; future native scheduled runs |

### Locale, time and hostname

The first interface supports `en_US.UTF-8` and `zh_TW.UTF-8`. `locale.generated`
must contain `locale.lang`, without duplicates. Other enabled locale.gen entries
and unowned locale.conf keys are preserved. Permanent `LC_ALL` is not exposed;
see [locale.conf](https://man.archlinux.org/man/locale.conf.5.en).

A missing generated locale is repaired even if locale.gen already matches.
If generation fails, the new LANG is not published. Repair the native generator
and rerun with the pending marker intact.

Time zones must name an existing native zoneinfo entry. A regular localtime file,
unexpected link, or local RTC mode stops adoption; inspect and resolve those
conditions explicitly. The adapter does not convert the hardware clock's mode.
The Host owns static and transient hostname when selected; configure other
hostname setters consistently to avoid repeated drift.

To opt into time synchronization, set `timeSync = { };` or add a `servers` list.
Only systemd-timesyncd is supported. Existing enabled/active chrony, ntpd or
OpenNTPD units conflict. An empty server list retains native server selection;
a custom list sets system servers but does not exclude per-link or fallback
sources. Check those sources when selecting servers. Waiting for an NTP response
is reported separately from successful service convergence.

### Journal, console and power

`journal.storage` accepts auto, persistent or volatile. Optional bounded fields
are `systemMaxUseMiB`, `systemKeepFreeMiB`, `runtimeMaxUseMiB` and
`maxRetentionDays`; omitted fields remain at native defaults. Selecting retention
can discard old logs during normal rotation. Successful configuration does not
promise immediate disk usage below the selected limit. No vacuum job is added.

Console requires a native `keymap`; `font` is optional. Both are validated
against installed kbd assets. An omitted font preserves the current FONT key.
Desktop keyboard configuration remains with Hyprland.

Power accepts `powerKey` (ignore, poweroff, suspend) and `lidSwitch` (ignore,
suspend), with at least one selected. These are logind event settings, not idle
policy. Hypridle remains responsible for desktop idle behavior. Desktop inhibitors
still determine whether logind handles an event; no inhibitor is overridden.
A pending receipt records the boot and desired content. Rerun after reboot to
clear it. No running login session is restarted to apply a setting.

### UFW adoption and recovery

The interface currently supports inbound TCP/UDP port or contiguous port-range
allows from anywhere, covering both IP families. It preserves the observed
Host's default policies. It does not expose arbitrary commands, routing rules,
interface names, or a second firewall provider.

Before first rollout:

1. Use a local console or an independently verified recovery path. Confirm the
   declared rules preserve the actual remote access path, including LAN/VPN use.
2. Inspect `sudo ufw status verbose` locally and review existing rule ownership.
   Confirm `/etc/default/ufw` has IPv6 enabled, `MANAGE_BUILTINS=no`, and the
   expected default policies. Conflicting policies require deliberate adoption;
   deployment does not silently rewrite them.
3. Preserve a private, root-readable recovery copy of `/etc/ufw` and
   `/etc/default/ufw` outside the repository and Nix store. Record the unit state
   and rules locally. These are operator recovery materials, not source inputs.
4. Check coexistence with actual Tailscale/libvirt rules and application traffic.
   The source VM models independent chains and NAT; it does not register a real
   Tailscale client or Runner and does not certify every local routing topology.

Deployment adopts matching rules without changing their comments or order and
adds missing rules through UFW. It checks both persisted UFW status and required
kernel rules/policies; missing kernel requirements trigger a UFW reload.
Restrictive DENY/REJECT/LIMIT rules require ownership review before automatic
addition, since their order can prevent the declared allow from working.
An enabled/active standalone nftables service is also an ownership conflict.
No reset, ruleset flush, unowned-rule deletion, or other service stop is used.
Removing a declaration does not retire the corresponding existing rule.

If application connectivity fails, use the prepared console to inspect the
specific rules and traffic. Restore the private UFW files and previous enabled
state as a deliberate recovery operation; reload UFW to apply restored files.
Do not flush the whole ruleset or delete Tailscale/libvirt tables. Verify IPv4,
IPv6 and the remote access path before ending the console session. Keep the
pending marker until a corrected declaration converges successfully.

### TRIM

Opt in with `trim = { };` only after selecting storage discard policy. Preflight
requires a mounted discard-capable block device, rejects mounted encrypted
storage, and checks for another apparent TRIM schedule. Review filesystem and
custom cron/service schedules as part of adoption; the check cannot infer the
intent of arbitrarily named operator scripts.

The adapter uses the native timer and a dedicated `Persistent=false` drop-in,
which prevents missed runs from being caught up immediately when the timer is
started. It preserves the package calendar and randomized delay. A conflicting
persistence override stops adoption. No immediate fstrim command is issued and
no crypttab, fstab, swap or kernel setting is changed.

## Conflicts and interrupted deployment

Shared files preserve unowned assignments and comments; malformed or duplicate
assignments stop adoption instead of being sourced as shell. Dedicated systemd
drop-ins reject conflicting keys in the effective configuration sources.
Managed files reject unsafe path components, symlinks and unexpected file types;
localtime has its own restricted symlink handling. Files compare content and
metadata before replacement.

System setting actions have private `system-<capability>.pending` markers under
`/var/lib/nix-config/arch/`. They are persisted before writes and cleared only
when the action succeeds. Fix prerequisites and rerun; do not delete pending
markers to make a failure disappear. A healthy repeat preserves file identities
and avoids service restarts. Power receipts intentionally remain until a later
boot. Unselecting a capability leaves its pending receipt and files alone.

Native command diagnostics identify the failed operation without printing raw
settings or native output. Inspect the relevant system configuration locally;
never attach credentials, Runner configuration or unrelated logs to a report.
These operations are recoverable steps, not a cross-service rollback transaction.

## Source validation

```bash
nix build --no-link .#checks.x86_64-linux.system-settings-interface
nix build --no-link .#checks.x86_64-linux.system-settings-tests
nix build --no-link .#checks.x86_64-linux.arch-switch-tests
nix build --no-link .#checks.x86_64-linux.system-firewall-integration
nix flake check
```

Fake-native tests use temporary roots for settings, metadata, failure recovery,
repeat execution and orchestration. The firewall check boots an isolated VM
with a pinned, private upstream UFW fixture and sends packets through network
namespaces. It never loads rules on the real host. It requires a builder capable
of running the NixOS VM test; keep the integration gate rather than substituting
a live-host check. Test-only UFW is not installed in the home or Arch inventory.
