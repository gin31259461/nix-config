{ inputs }:
{
  system,
  hostName,
  platform,
  hardware,
  capabilities ? null,
  username,
  user,
  ai ? {
    enable = false;
  },
}:
let
  pkgs = import inputs.nixpkgs {
    inherit system;
    config.allowUnfree = true;
  };
  profileRegistry = import ../profiles;
  moduleRegistry = import ../modules/home;
  resolve =
    registry: kind: name:
    if builtins.hasAttr name registry then registry.${name} else throw "unknown ${kind}: ${name}";
in
assert inputs.nixpkgs.lib.assertMsg (platform == "arch") "unsupported platform: ${platform}";
inputs.home-manager.lib.homeManagerConfiguration {
  inherit pkgs;

  extraSpecialArgs = {
    inherit
      inputs
      hostName
      platform
      hardware
      capabilities
      ;
  };

  modules = [
    {
      home = {
        inherit username;
        homeDirectory = user.homeDirectory;
        stateVersion = user.stateVersion;
      };

      programs.home-manager.enable = true;
    }
  ]
  ++ [
    (import ../modules/ai {
      lib = inputs.nixpkgs.lib;
      config = ai;
    }).homeModule
  ]
  ++ [ (user.homeConfig or { }) ]
  ++ [
    ({ lib, ... }: {
      options.workstation.capabilities = lib.mkOption {
        type = lib.types.attrsOf (
          lib.types.submodule {
            options.enable = lib.mkOption {
              type = lib.types.bool;
              default = true;
            };
          }
        );
        default = { };
        internal = true;
      };
      config.workstation.capabilities = lib.genAttrs [ "keepassxc" "noctalia-config" ] (name: {
        enable = builtins.elem name user.modules;
      });
    })
  ]
  ++ [
    ../modules/home/keepassxc.nix
    ../modules/home/noctalia-config
  ]
  ++ user.homeModules
  ++ map (resolve profileRegistry "profile") (
    builtins.filter (
      name: capabilities == null || capabilities.desktop.enable || name != "workstation"
    ) user.profiles
  )
  ++ map (resolve moduleRegistry "home module") user.modules;
}
