# Configure the workstation

Edit [configuration.nix](../configuration.nix). It is the single selected Host
module and imports [Host defaults](../hosts/arch/default.nix). Flake output wiring
and deployment scripts do not need to change when selecting capabilities.
This uses the Nixpkgs module system on Arch; it does not accept arbitrary NixOS
modules or provide NixOS system activation.

## Change a value

Keep the import and add ordinary definitions:

```nix
{ ... }:
{
  imports = [ ./hosts/arch ];

  networking.firewall.enable = false;
  services.fstrim.enable = false;
  virtualisation.kvm.gui.enable = false;
  programs.vicinae.enable = false;
  time.timeZone = "UTC";

  users.users.abnertu.home.programs.git.enable = false;
}
```

The [option schema](../lib/configuration-options.nix) owns types and reusable
option defaults. Host modules use `lib.mkDefault` for reviewed machine values.
An ordinary definition replaces a `mkDefault`; file order is not an override
mechanism. Conflicting ordinary scalar definitions are errors. Lists at the same
priority merge; use `lib.mkBefore`/`lib.mkAfter` for ordering and `lib.mkForce`
when an intentional replacement must beat other ordinary definitions.

Additional imports are explicit Nix modules. Use `users.users.<name>.home` for
Home Manager options, or `homeModules` for additional file imports. Home Manager
has its own option schema; its upstream defaults and safety assertions still
apply. Required `homeDirectory`, `stateVersion` and account description belong
to the login declaration. Do not bump `stateVersion` as part of routine upgrades.

Read an individual resolved value without touching live state:

```bash
nix eval .#configurations.arch.networking.hostName
nix eval .#configurations.arch.services.fstrim.enable
nix eval --json .#configurations.arch.networking.firewall
```

`configurations` is a custom inspection output; `nix flake check` reports an
unknown-output warning for it while validating the standard checks and builds.
The evaluator uses module class `nixConfig`, so importing a module with an
incompatible declared class fails. Unknown option names and wrong types fail
configuration evaluation.

## Select capabilities

Every public capability `enable` defaults to **true**. These are meaningful
feature or bundle boundaries, not a switch per dependency package. Fixed Runner
security and mandatory identity values are deliberately not configurable switches.
An empty Runner instance set creates no controller, accounts or requirements.

| Namespace | Selection |
| --- | --- |
| `networking` | `hostName`, `hostname.enable`, `networkmanager.enable`, `firewall.enable` and rules |
| `i18n`, `time`, `console` | Locale generation, time zone and virtual-console settings, each with `enable` |
| `services` | `timesyncd`, `journald`, `logind`, `fstrim`, `powerProfilesDaemon`, `tailscale`, `gitlabRunner` |
| `hardware` | Declared graphics, `openrazer.enable`, `bluetooth.enable`, `initramfs.enable`, modules and images |
| `programs.ai` | Parent enable, Codex package and skill preset children |
| `programs` | `sunshine.enable`, `vesktop.enable`, `vicinae.enable` |
| `virtualisation` | Parent enable, KVM, KVM GUI and Podman children |
| `desktop` | Parent enable; polkit agent, overview and Tailscale tray children |
| `users.users.<name>.profiles` | An enable per registered portable bundle |
| `users.users.<name>.modules` | An enable per registered shared home capability |
| `services.gitlabRunner.instances.<name>` | Instance enable and Runner-owned instance values |

Use [profile](../profiles/default.nix), [home Module](../modules/home/default.nix),
[native package](../platforms/arch/packages.nix) and
[native service](../platforms/arch/services.nix) inventories as the authoritative
lists. The desktop parent suppresses workstation home behavior and native desktop
bundles. Machine Bluetooth, networking and other independently selected services
remain independent. User home Module switches select home behavior, not native
package removal; the Arch desktop bundle owns shared desktop dependencies.

The deployment profile labels the full user composition. To disable its selected
profile, also select an enabled profile as `deployment.profile`. Setting
`desktop.enable = false` suppresses desktop realization while retaining that
composition label. Runner Podman requirements remain independent of the login
user's virtualization switch.

## Understand disabling

For Arch, false withdraws that capability's desired packages, managed files and
runtime actions. Existing packages, services, rules, registrations and pending
receipts remain untouched. Disabling Sunshine also stops querying or configuring
its repository, but preserves an existing repository declaration. Disabling
initramfs management preserves both its marked addition and pending rebuild.

Home Manager builds a new generation without disabled managed units or links;
activation can remove those previously managed links and apply its normal unit
transition behavior. This is not application-data cleanup. Turning off KeePassXC
startup or Noctalia preference exchange does not read or delete their runtime data.
Noctalia storage preparation remains a separately selected home Module.

## Review new defaults before deployment

The supplied Host now selects time synchronization, journal management, console,
logind event policy and TRIM through their default-on switches. The initial
values use native time servers, journal `auto` storage, US console keymap,
power-key `poweroff`, lid-switch `suspend`, and the no-catch-up native TRIM timer.
The Host overrides the time zone to Asia/Taipei and generates English and
Traditional Chinese UTF-8 locales.

Read [system settings](system-settings.md) before activating these declarations.
Existing time daemons, encrypted/discard storage, firewall ownership or conflicting
native settings can block adoption. Choose false for capabilities you want left
unmanaged; a successful source build neither inspects nor adopts the live machine.

Validate changes with the [development commands](../README.md#develop-and-validate).
Use [deployment](deployment.md) only when ready to apply them deliberately.
