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

## Live configuration development mode

By default, Neovim and Hyprland configurations are immutable inputs pinned in `flake.nix` (`nvim-config` and `hypr-config`), projected into `~/.config/nvim` and `~/.config/hypr` through Home Manager with safety preflights that reject projections targeting Git worktrees or backup suffixes.

To enable live local editing directly against local Git worktrees without store rebuilds or activation preflight errors, declare user `development` absolute paths in `configuration.nix`:

```nix
users.users.abnertu.development = {
  neovimPath = "/home/abnertu/path/to/nvim-config";
  hyprlandPath = "/home/abnertu/path/to/hypr-config";
};
```

When a development path is set:
- Home Manager uses `mkOutOfStoreSymlink` to link directly to the specified worktree path instead of the pinned Nix store derivation.
- Projection safety checks for that target are bypassed so Home Manager does not reject linking to a local Git worktree.
- Changes in the local worktree take effect immediately in live editor or window manager reload cycles without requiring `just arch-workstation` or `home-switch`.
- Setting a path back to `null` (or omitting it) restores the pinned external flake input and strict worktree protection.
