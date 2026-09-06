# Desktop session

UWSM starts Hyprland and owns the graphical session. Arch supplies the desktop
executables; Home Manager supplies their user-unit policy. Keep one startup
owner per application and use package-unit drop-ins at canonical unit names.

## Login and tray behavior

KeePassXC opens its database minimized at login and unlocks manually. Startup
waits for `IsStatusNotifierHostRegistered` for approximately ten seconds, then
allows degraded startup if the tray is unavailable. It neither receives a
password nor restarts automatically to repair an icon.

Noctalia starts independently of KeePassXC. Tray consumers start after Noctalia;
Vicinae also waits for the watcher with a bounded timeout. Vicinae stops before
Noctalia and starts after it, preventing the launcher from claiming
`org.kde.StatusNotifierWatcher` during a shell restart. Restarting Noctalia
briefly closes the launcher and panel, but does not restart Vesktop or KeePassXC.
Remmina's background applet is disabled.

Vesktop uses `--ozone-platform=x11` in its service and
`~/.config/vesktop-flags.conf`. This app-specific compatibility setting restores
repeated close-to-tray and reopen behavior on the tested Vesktop 1.6.7 /
Hyprland 0.56.2 combination. XWayland can affect scaling and input; re-test native
Wayland after relevant upgrades before removing the setting.

For an operator tray check, compare the watcher's PID with Noctalia:

```bash
busctl --user call org.freedesktop.DBus /org/freedesktop/DBus \
  org.freedesktop.DBus GetConnectionUnixProcessID s org.kde.StatusNotifierWatcher
systemctl --user show noctalia.service -p MainPID
```

An item list alone does not establish ownership. After a deliberate shell
restart, check the launcher and tray, then close and reopen Vesktop without
changing its PID. `Vesktop is already running. Quitting...` from a second process
is normal if the original window appears. Cold-boot KeePassXC tray display and
shell-restart behavior have been manually verified.

## Passwords and encrypted storage

The Host selects KeePassXC and Noctalia storage separately.
[keepassxc.nix](../modules/home/keepassxc.nix) owns process startup; the
[user configuration](../homes/abnertu/home.nix) supplies its runtime database
filename. GUI settings and database protection remain local.

[noctalia-storage.nix](../modules/home/noctalia-storage.nix) selects file-backed
storage and disables calendar synchronization. The runtime key is
`~/.local/share/noctalia/file-key-v1/master-key`. Its directory is mode `0700`,
and its key and markers are mode `0600`, owned by the login user. Only the path
enters Nix artifacts; key contents and encrypted data stay outside Git and the
Nix store.

Back up the key securely with the data it protects. A process that can read
both can decrypt Noctalia data even while KeePassXC is locked. A new key cannot
recover data encrypted with a lost key. Other applications or plugins can still
request Secret Service access; file-backed storage is not a global ban on
unlock prompts.

## Prepare storage on a new home

First activation requires Noctalia to be stopped. Keep a terminal open;
Hyprland and existing application windows can remain running:

```bash
systemctl --user stop noctalia.service
nix run .#arch-workstation && systemctl --user start noctalia.service
```

Use the deployment's `--update` mode if native packages are missing. The
activation guard does not stop services itself. Do not launch a tray consumer
that pulls Noctalia back in during preparation.

Preparation generates a key once and preserves existing encrypted data offline:

| Existing directory | Archive |
| --- | --- |
| `~/.local/state/noctalia/clipboard` | `~/.local/state/noctalia/clipboard.before-file-key` |
| `~/.cache/noctalia/calendar` | `~/.cache/noctalia/calendar.before-file-key` |

Archives are renamed without decryption or deletion. They require their original
key for recovery; new history uses the new file key. Existing settings, unrelated
state and old keys remain untouched. Dry-run activation creates no key or archive.

## Recover storage safely

Preparation records `pending` before changes and `ready` when complete, under
`~/.local/share/noctalia/file-key-v1/`. A persistent lock serializes changes.
Repeat activation preserves the published key and application data.

| Failure | Recovery |
| --- | --- |
| Noctalia running during initial preparation | Stop the service and retry |
| Conflicting storage overrides, calendar accounts or includes | Review the exact local settings; resolve intent before retrying |
| Custom Noctalia roots | Establish ownership explicitly before changing paths |
| Archive collision or symlink | Preserve both locations and resolve ownership |
| Interrupted preparation | Keep markers, lock and published key; stop Noctalia and rerun deployment |
| `ready` exists but key is missing | Restore the exact key from secure backup; never force regeneration |
| Incorrect ownership or permissions | Restore login-user ownership and the required `0700`/`0600` modes |

Do not restart Noctalia until preparation or recovery succeeds. A Home Manager
rollback does not reverse data changes. Restoring archived history requires a
separate offline restoration of its matching key and configuration, preserving
any new history.

After login, expect both services active and the vault locked until you unlock
it deliberately:

```bash
systemctl --user is-active noctalia.service keepassxc.service
```

Closing KeePassXC must not stop Noctalia. Investigate unexpected prompts through
the requesting application's startup behavior without dumping credentials,
KeePassXC INI files or D-Bus secret payloads. Preference capture and GUI override
recovery are covered in [Noctalia preferences](noctalia-config.md).
