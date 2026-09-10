# Arch system settings

System settings are selected through `configuration.nix` and realized by the
privileged adapter under `platforms/arch/system/`. Home Manager does not manage
these system files or services.

## Managed capabilities

| Capability | Scope |
| --- | --- |
| `i18n` | Generated locales and `LANG` |
| `time` | System timezone |
| `networking.hostname` | Static and transient hostname |
| `services.timesyncd` | systemd-timesyncd policy |
| `services.journald` | Journal storage and retention |
| `console` | Virtual-console keymap and font |
| `services.logind` | Power-key and lid-event policy |
| `networking.firewall` | UFW policy and declared rules |
| `services.fstrim` | Native fstrim timer policy |
| `networking.hotspot` | Prepared NetworkManager AP settings |

Disabled capabilities contribute no desired runtime action and do not undo
previously managed state.

## Preflight

System preflight is a core deployment stage. It validates ownership, required
native commands, files, units and settings before mutation. Conflicts are fatal;
core system settings are never skipped as optional modules.

Review live ownership before first enabling a capability. In particular, confirm
that time synchronization, storage discard policy, console assets, NetworkManager
and UFW are compatible with the declarations you select.

For firewall changes, inspect current UFW policy from a local recovery-capable
session before deployment:

```bash
sudo ufw status verbose
```

Hotspot-specific behavior is documented in [hotspot](hotspot.md).

## Pending actions

Actions that must follow a system write use pending markers under:

```text
/var/lib/nix-config/arch/
```

Markers are created before mutation and cleared only after the associated action
succeeds. Correct a failure and rerun deployment with the marker intact.

Healthy repeat deployment compares content, ownership, mode and runtime state.
Unchanged files are not rewritten and healthy services are not restarted merely
because deployment runs again. Logind changes wait for a boot boundary instead of
restarting active login sessions.

## Diagnostics

System commands use the shared native adapter. Failed commands report the exact
command, exit status, stdout and stderr. Timeout errors preserve partial output.

```bash
just arch-workstation verbose
```

Verbose mode prints each native command and its captured output. Unexpected
adapter exceptions retain their concrete exception type/message and include a
Python traceback in verbose mode.

Keep credentials, private keys and unrelated application data out of diagnostic
reports.

## Validate

```bash
nix build --no-link --show-trace --print-build-logs \
  .#checks.x86_64-linux.system-settings-interface \
  .#checks.x86_64-linux.system-settings-tests \
  .#checks.x86_64-linux.arch-switch-tests \
  .#checks.x86_64-linux.system-firewall-integration
just check
```

Checks use temporary roots, fake native commands and isolated test environments;
they do not change the real workstation.
