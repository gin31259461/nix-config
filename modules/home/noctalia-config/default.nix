{
  config,
  lib,
  pkgs,
  hostName,
  ...
}:
{
  options.workstation.noctalia.preferencesFile = lib.mkOption {
    type = lib.types.path;
    description = "Reviewed, non-secret Noctalia user preferences in the repository.";
  };
  config = {
    xdg.configFile."noctalia/config.toml".source = config.workstation.noctalia.preferencesFile;
    home.packages = [
      (import ./package.nix {
        inherit pkgs;
        username = config.home.username;
        homeConfiguration = "${config.home.username}@${hostName}";
      })
    ];
  };
}
