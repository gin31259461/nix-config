{ lib, raw }:
let
  fields =
    context: allowed: value:
    assert lib.assertMsg (builtins.isAttrs value) "${context} must be an attribute set";
    assert lib.assertMsg (
      lib.subtractLists allowed (builtins.attrNames value) == [ ]
    ) "${context} has unknown fields";
    value;
  host = fields "host" [
    "name"
    "platform"
    "system"
    "deployment"
    "users"
    "gitlabRunners"
    "hardware"
    "ai"
    "virtualization"
    "systemSettings"
  ] raw;
  deployment = fields "deployment" [ "username" "profile" ] host.deployment;
  hardware = fields "hardware" [
    "graphics"
    "openrazer"
    "initramfsModules"
    "initramfsImages"
  ] host.hardware;
  users = lib.mapAttrs (
    name: rawUser:
    fields "user ${name}" [
      "description"
      "homeDirectory"
      "stateVersion"
      "admin"
      "groups"
      "profiles"
      "modules"
      "homeModules"
    ] rawUser
  ) host.users;
in
# Local types, enums, ranges and path formats belong to configuration-options.nix.
# This private validator retains only normalized shape and cross-field invariants.
assert lib.assertMsg (
  host.platform == "arch" && host.system == "x86_64-linux"
) "only x86_64 Arch hosts are supported";
assert lib.assertMsg (
  builtins.hasAttr deployment.username users
) "unknown deployment user";
assert lib.assertMsg users.${deployment.username}.admin "deployment user must be an administrator";
assert lib.assertMsg (builtins.elem deployment.profile
  users.${deployment.username}.profiles
) "deployment profile must be selected by its user";
assert lib.assertMsg (
  let
    homes = map (user: user.homeDirectory) (builtins.attrValues users);
  in
  builtins.length homes == builtins.length (lib.unique homes)
) "login users must have distinct home directories";
builtins.deepSeq users (
  host
  // {
    inherit users hardware deployment;
    ai = import ../modules/ai/interface.nix {
      inherit lib;
      raw = host.ai or { };
    };
    virtualization = import ../modules/virtualization/interface.nix {
      inherit lib;
      raw = host.virtualization or { };
    };
    systemSettings = import ./system-settings.nix {
      inherit lib;
      raw = host.systemSettings or { };
    };
    gitlabRunners = host.gitlabRunners or { };
  }
)
