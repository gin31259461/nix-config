{ inputs }:
{
  system,
  hostName,
  platform,
  username,
  user,
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
    inherit inputs hostName platform;
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
  ++ user.homeModules
  ++ map (resolve profileRegistry "profile") user.profiles
  ++ map (resolve moduleRegistry "home module") user.modules;
}
