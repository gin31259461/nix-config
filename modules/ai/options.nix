{ lib }:
let
  enable = description: (lib.mkEnableOption description) // { default = true; };
in
{
  enable = (lib.mkEnableOption "ai") // {
    default = true;
  };
  codex.enable = lib.mkOption {
    type = lib.types.bool;
    default = true;
  };
  skillsPresets.enable = lib.mkOption {
    type = lib.types.bool;
    default = true;
  };
  ollama = {
    enable = enable "Ollama";
    keepAlive = lib.mkOption {
      type = lib.types.ints.between (-1) 2147483647;
      default = -1;
      description = "Default model residency in seconds; -1 keeps loaded models resident.";
    };
    vulkan = {
      enable = enable "the Ollama Vulkan backend";
      visibleDevices = lib.mkOption {
        type = lib.types.nullOr (lib.types.nonEmptyListOf lib.types.ints.unsigned);
        default = null;
        description = "Reviewed Ollama Vulkan device IDs; null requires selection before deployment.";
      };
    };
    proxy = {
      enable = enable "the Caddy and Tailscale Serve proxy for Ollama";
      httpsPort = lib.mkOption {
        type = lib.types.ints.between 1 65535;
        default = 443;
        description = "Tailnet HTTPS port used by Tailscale Serve.";
      };
    };
  };
}
