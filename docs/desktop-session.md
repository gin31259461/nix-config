# Desktop session

UWSM starts Hyprland and owns the graphical session. Arch supplies native desktop
executables; Home Manager supplies user configuration and user-service policy.
Keep one startup owner for each application.

## Managed applications

Desktop capabilities are selected through `desktop.enable`, program switches and
`users.users.<name>.modules`. Shared behavior lives under `modules/home/`.
Disabling a user capability removes its managed Home Manager contribution from
the next generation; it does not delete application data.

- **Noctalia**: Starts independently and owns the StatusNotifier watcher. Tray
  consumers start after the shell.
- **Vicinae**: Configured with bounded degraded startup so a missing or delayed tray
  watcher does not block the session.
- **Vesktop**: Keeps its application-specific compatibility flags in its own service/configuration.
- **Sunshine**: Configured with `capture = wlr` to stream the Wayland desktop directly
  without prompting a share picker on login.
- **Password Store**: Managed via `pass` (`programs.password-store`) in the development
  profile, integrated with GPG and Git credential helpers.

## Noctalia storage initialization

Noctalia file-backed storage uses a local master key under:

```text
~/.local/share/noctalia/file-key-v1/master-key
```

The master key and encrypted application data remain outside Git and the Nix store.
Back up the key together with the data it protects.

On a new home, stop Noctalia before the first activation:

```bash
systemctl --user stop noctalia.service
just arch-workstation
systemctl --user start noctalia.service
```

The activation prepares storage once and records its state below
`~/.local/share/noctalia/file-key-v1/`. Existing clipboard/calendar directories
that require isolation are moved to their defined archive locations before the
new storage state is published. Existing archive collisions, symlinks, or
conflicting overrides stop activation.

A `ready` marker with a missing key is not permission to generate another key.
Restore the original key from backup. Recover an interrupted initialization by
keeping the key, markers, and archived data intact, stopping Noctalia, and
rerunning activation.

## Verify the session

```bash
systemctl --user is-active noctalia.service
busctl --user call org.freedesktop.DBus /org/freedesktop/DBus \
  org.freedesktop.DBus GetConnectionUnixProcessID s org.kde.StatusNotifierWatcher
systemctl --user show noctalia.service -p MainPID
```

The watcher PID should correspond to Noctalia. Shell restarts should not
restart unrelated applications merely to restore tray state.

## Source validation

Graphical-session tests use synthetic Home Manager configurations and do not
connect to the real desktop. Process overview tests use fake command signals and
preserve the last valid state when native queries fail. Run:

```bash
just check
```

Noctalia preference capture and deployment is documented separately in
[Noctalia configuration](noctalia-config.md).
