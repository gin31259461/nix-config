# Desktop session

UWSM starts Hyprland and owns the graphical session. Arch supplies native executables; Home Manager supplies managed user configuration and user-service policy. Give each application one startup owner. The desktop and user capability switches in `configuration.nix` choose which contributions appear in the next home generation; disabling one does not erase application data.

Noctalia owns the StatusNotifier watcher, and tray consumers start after it. Vicinae uses bounded degraded startup when the watcher is delayed. Vesktop keeps its compatibility flags in its own service. Sunshine uses Wayland `wlr` capture. The development profile uses `pass` through `programs.password-store` with GPG and Git credential helpers. The owning modules define the exact current packages and service units.

## Noctalia storage first activation

Noctalia's file-backed encrypted storage keeps its master key under `~/.local/share/noctalia/file-key-v1/`, outside Git and the Nix store. Back up the key with the data it protects. On a new home, stop Noctalia before the first activation:

```bash
systemctl --user stop noctalia.service
just arch-workstation
systemctl --user start noctalia.service
```

Activation prepares storage once. Existing clipboard and calendar directories that require isolation move to defined archive locations before the new state is published. Archive collisions, symlinks and conflicting overrides stop activation. A `ready` marker with a missing key is not permission to create a replacement: restore the original key. For an interrupted initialization, keep the key, markers and archives intact, stop Noctalia and rerun activation.

## Inspect the session

```bash
systemctl --user is-active noctalia.service
busctl --user call org.freedesktop.DBus /org/freedesktop/DBus \
  org.freedesktop.DBus GetConnectionUnixProcessID s org.kde.StatusNotifierWatcher
systemctl --user show noctalia.service -p MainPID
```

The watcher PID should belong to Noctalia. Shell restarts should not restart unrelated applications merely to restore the tray. The [Noctalia configuration guide](noctalia-config.md) covers preference capture and deployment separately from encrypted storage. Source tests use synthetic Home Manager configurations and fake commands; run `just check` without connecting to the live desktop.
