{ lib, raw }:
let
  fields =
    context: allowed: value:
    assert lib.assertMsg (builtins.isAttrs value) "${context} must be an attribute set";
    assert lib.assertMsg (
      lib.subtractLists allowed (builtins.attrNames value) == [ ]
    ) "${context} has unknown fields";
    value;
  named = value: builtins.isString value && builtins.match "[a-z][a-z0-9_-]*" value != null;
  strings = value: builtins.isList value && lib.all builtins.isString value;
  host = fields "host" [
    "name"
    "platform"
    "system"
    "deployment"
    "users"
    "gitlabRunners"
    "hardware"
  ] raw;
  deployment = fields "deployment" [ "username" "profile" ] host.deployment;
  hardware = fields "hardware" [
    "graphics"
    "openrazer"
    "initramfsModules"
    "initramfsImages"
  ] host.hardware;
  profiles = import ../profiles;
  modules = import ../modules/home;
  users = lib.mapAttrs (
    name: rawUser:
    let
      user = fields "user ${name}" [
        "description"
        "homeDirectory"
        "stateVersion"
        "admin"
        "groups"
        "profiles"
        "modules"
        "homeModules"
      ] rawUser;
    in
    assert lib.assertMsg (named name) "invalid login username";
    assert lib.assertMsg (builtins.isBool user.admin) "user.admin must be boolean";
    assert lib.assertMsg (
      builtins.isString user.homeDirectory && lib.hasPrefix "/home/" user.homeDirectory
    ) "login home must be under /home";
    assert lib.assertMsg (
      builtins.isString user.stateVersion
      && builtins.match "[0-9]{2}\\.[0-9]{2}" user.stateVersion != null
    ) "invalid Home Manager stateVersion";
    assert lib.assertMsg (strings user.groups && lib.all named user.groups) "invalid login groups";
    assert lib.assertMsg (
      strings user.profiles && lib.all (name: builtins.hasAttr name profiles) user.profiles
    ) "unknown profile";
    assert lib.assertMsg (
      strings user.modules && lib.all (name: builtins.hasAttr name modules) user.modules
    ) "unknown home module";
    assert lib.assertMsg (
      builtins.isList user.homeModules && lib.all builtins.isPath user.homeModules
    ) "homeModules must contain Nix paths";
    user
  ) host.users;
in
assert lib.assertMsg (named host.name) "invalid host name";
assert lib.assertMsg (
  host.platform == "arch" && host.system == "x86_64-linux"
) "only x86_64 Arch hosts are supported";
assert lib.assertMsg (
  named deployment.username && builtins.hasAttr deployment.username users
) "unknown deployment user";
assert lib.assertMsg users.${deployment.username}.admin "deployment user must be an administrator";
assert lib.assertMsg (builtins.elem deployment.profile
  users.${deployment.username}.profiles
) "deployment profile must be selected by its user";
assert lib.assertMsg (builtins.elem hardware.graphics [
  "amd"
  "generic"
]) "unsupported graphics selection";
assert lib.assertMsg (builtins.isBool hardware.openrazer) "hardware.openrazer must be boolean";
assert lib.assertMsg (
  strings hardware.initramfsModules
  && lib.all (value: builtins.match "[a-zA-Z0-9_-]+" value != null) hardware.initramfsModules
) "invalid initramfs modules";
assert lib.assertMsg (
  strings hardware.initramfsImages
  && hardware.initramfsImages != [ ]
  && lib.all (
    value: lib.hasPrefix "/boot/" value && !lib.hasInfix ".." value
  ) hardware.initramfsImages
) "initramfs images must be under /boot";
builtins.deepSeq users (
  host
  // {
    inherit users hardware deployment;
    gitlabRunners = host.gitlabRunners or { };
  }
)
