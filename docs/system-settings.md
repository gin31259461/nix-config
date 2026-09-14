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
previously managed state. Destructive retirement is always separate from merely
withdrawing management.

## Firewall ownership and scope

Firewall rules accept a stable `owner`, an optional ingress `interface`, an
optional `source`, and an explicit lifecycle `state` (`present` or `absent`).
Keep rules as narrowly scoped as the service contract permits. For example:

```nix
networking.firewall.rules = [
  {
    owner = "example-lan-service";
    protocol = "tcp";
    fromPort = 8443;
    interface = "enp14s0";
    source = "192.168.1.0/24";
  }
];
```

Existing matching operator rules can satisfy a `present` declaration, but they
are not automatically claimed. The adapter records a root-owned receipt only for
rules it actually creates. `state = "absent"` may delete only a rule for which
that receipt exists; it never interprets `enable = false` or declaration removal
as permission to delete arbitrary UFW state.

The current host rules intentionally retain their historical global reach because
the repository does not encode enough service topology to infer a safe source or
interface. Scope those rules only after deciding which network each service is
supposed to accept traffic from.

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
