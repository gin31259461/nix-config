{ lib }:
let
  inventory = import ./artifacts.nix;
  enable = description: (lib.mkEnableOption description) // { default = true; };
  port = lib.types.ints.between 1 65535;
in
{
  enable = enable "ai";
  codex.enable = enable "Codex";
  skillsPresets.enable = enable "the repository skill presets";
  llama = {
    enable = enable "llama.cpp";
    model = {
      name = lib.mkOption {
        type = lib.types.enum (builtins.attrNames inventory.models);
        default = inventory.defaultModel;
      };
      device = lib.mkOption { type = lib.types.strMatching "(ROCm|Vulkan)[0-9]+"; };
      contextSize = lib.mkOption {
        type = lib.types.nullOr lib.types.ints.positive;
        default = null;
      };
      fitTarget = lib.mkOption {
        type = lib.types.nullOr lib.types.ints.positive;
        default = null;
      };
      cacheTypeK = lib.mkOption {
        type = lib.types.nullOr (
          lib.types.enum [
            "f16"
            "q8_0"
            "q4_0"
          ]
        );
        default = null;
      };
      cacheTypeV = lib.mkOption {
        type = lib.types.nullOr (
          lib.types.enum [
            "f16"
            "q8_0"
            "q4_0"
          ]
        );
        default = null;
      };
      batchSize = lib.mkOption {
        type = lib.types.nullOr lib.types.ints.positive;
        default = null;
      };
      microBatchSize = lib.mkOption {
        type = lib.types.nullOr lib.types.ints.positive;
        default = null;
      };
      parallel = lib.mkOption {
        type = lib.types.nullOr lib.types.ints.positive;
        default = null;
      };
    };
    proxy = {
      enable = enable "the Caddy and Tailscale Serve proxy for llama.cpp";
      httpsPort = lib.mkOption {
        type = port;
        default = 443;
      };
    };
  };
}
