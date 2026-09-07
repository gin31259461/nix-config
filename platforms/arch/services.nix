# Arch owns native workstation service realization.
{ lib, capabilities }:
lib.optional capabilities.networking "NetworkManager.service"
++ lib.optional capabilities.bluetooth "bluetooth.service"
++ lib.optional capabilities.power "power-profiles-daemon.service"
++ lib.optional capabilities.tailscale "tailscaled.service"
