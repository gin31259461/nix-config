{
  lib,
  raw ? { },
}:
let
  config = lib.evalModules {
    modules = [
      ({ lib, ... }: {
        options = {
          enable = lib.mkEnableOption "ai";
          codex.enable = lib.mkOption {
            type = lib.types.bool;
            default = true;
          };
          skillsPresets.enable = lib.mkOption {
            type = lib.types.bool;
            default = true;
          };
        };
      })
      raw
    ];
  };
in
builtins.deepSeq config.config config.config
