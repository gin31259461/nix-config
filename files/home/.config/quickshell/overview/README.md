# Quickshell workspace overview

This checked-in Hyprland overview shows workspaces and live window previews with keyboard navigation and drag-and-drop. Its source lives under `files/home/.config/quickshell/overview/`; the workstation's Home Manager file module projects it into the selected user's home. The graphical-session module owns `quickshell-overview.service`. Do not clone another copy into the managed runtime path or add a second Hyprland startup entry.

![Overview screenshot](assets/image.png)

## Use

When `desktop.overview.enable` is selected and the home generation is active, UWSM and the user service start the overview. The current IPC controls are:

```bash
qs ipc -c overview call overview toggle
qs ipc -c overview call overview open
qs ipc -c overview call overview close
```

The module supports clicking a window to focus it, middle-clicking to close it, dragging windows between workspaces, arrow-key navigation and Escape/Enter to close. Edit this repository's `common/Config.qml` for grid dimensions and scale, or `common/Appearance.qml` for visual style, then build and activate the next home generation. Changes made only in the managed runtime path may be replaced by activation.

## Validate source

```bash
nix build --no-link --show-trace --print-build-logs \
  .#checks.x86_64-linux.overview-refresh
```

The overview's query and refresh tests use fake signals and preserve the last valid state after a native query failure. The wider session behavior is covered by `just check` and [desktop session](../../../../../docs/desktop-session.md).

This component was adapted from the overview in [illogical-impulse](https://github.com/end-4/dots-hyprland) by end-4 and the standalone [quickshell-overview](https://github.com/Shanu-Kumawat/quickshell-overview) project. Preserve upstream attribution when redistributing.
