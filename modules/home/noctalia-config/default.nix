{
  config,
  lib,
  pkgs,
  hostName,
  inputs,
  ...
}:
{
  options.workstation.noctalia.preferencesFile = lib.mkOption {
    type = lib.types.path;
    description = "Reviewed, non-secret Noctalia user preferences in the repository.";
  };
  config = lib.mkIf (config.workstation.capabilities.noctalia-config.enable or true) {
    xdg.configFile."noctalia/config.toml".source = config.workstation.noctalia.preferencesFile;
    home.packages = [
      (import ./package.nix {
        inherit pkgs;
        adapterPython = inputs.nix-adapter.packages.${pkgs.stdenv.hostPlatform.system}.adapterPython;
        username = config.home.username;
        homeConfiguration = "${config.home.username}@${hostName}";
      })
    ];
  };
}
