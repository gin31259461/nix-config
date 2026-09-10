# Configuration

Edit `configuration.nix`. It is the selected Host entry and imports the reviewed
machine defaults from `hosts/arch`.

```nix
{ ... }:
{
  imports = [ ./hosts/arch ];

  networking.firewall.enable = false;
  services.fstrim.enable = false;
  virtualisation.kvm.gui.enable = false;
  time.timeZone = "UTC";
}
```

Host values use `lib.mkDefault`. Ordinary definitions in `configuration.nix`
override those defaults. Unknown option names, wrong types and invalid
combinations fail evaluation. Import order is not an override mechanism.

## Inspect resolved values

```bash
nix eval .#configurations.arch.networking.hostName
nix eval .#configurations.arch.services.fstrim.enable
nix eval --json .#configurations.arch.networking.firewall
```

The public schema is defined by `lib/configuration-options.nix` and feature-owned
interfaces under `modules/`. `lib/eval-configuration.nix` normalizes evaluated
values into the private Host and adapter interfaces.

## Main capability groups

| Namespace | Responsibility |
| --- | --- |
| `networking` | Hostname, NetworkManager, hotspot and firewall |
| `i18n`, `time`, `console` | Locale, timezone and virtual console |
| `services` | Time sync, journal, logind, TRIM, power, Tailscale and GitLab Runner |
| `hardware` | Graphics, Bluetooth, OpenRazer and initramfs intent |
| `programs.ai` | llama.cpp, Codex and shared AI skill presets |
| `programs` | Sunshine, Vesktop and Vicinae |
| `virtualisation` | KVM, virt-manager/libvirt and Podman |
| `desktop` | Graphical session and desktop-owned services |
| `users.users.<name>` | Human account profile and Home Manager composition |

Parent/child capability switches gate the resources owned by that capability.
GitLab Runner instances remain independent from the login user's virtualization
selection.

## Home Manager overrides

User-specific Home Manager values live under `users.users.<name>.home`. Reusable
behavior belongs in `profiles/` or `modules/home/`; machine-specific differences
belong in `homes/` or the Host declaration.

Do not change Home Manager `stateVersion` as part of routine updates. Human
accounts must be provisioned before deployment; service accounts are owned by
their modules.

## Disable semantics

For Arch-native capabilities, `enable = false` withdraws desired management. It
does not uninstall already installed packages, delete files, stop unrelated
runtime state or clear pending actions.

For Home Manager, the next generation omits disabled managed links and units and
uses normal Home Manager transition behavior. Application data is not deleted.

An optional module that remains enabled but requires preparation is handled by
its adapter readiness contract. If it has never been prepared, deployment may
skip that module. Invalid prepared state is an error.

## Validate

```bash
just check-fast
just check
just build
```

Use [deployment](deployment.md) only after source evaluation and checks pass.
System ownership and adoption requirements are documented in
[system settings](system-settings.md).
