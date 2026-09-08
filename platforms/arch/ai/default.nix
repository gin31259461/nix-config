{
  pkgs,
  config,
  hardware,
  tailscale,
}:
let
  ollama = config.enable && config.ollama.enable;
  vulkan = ollama && hardware.graphics == "amd" && config.ollama.vulkan.enable;
  proxy = ollama && config.ollama.proxy.enable && tailscale;
in
{
  inherit ollama vulkan proxy;
  manifest = pkgs.writeText "arch-ai.json" (
    builtins.toJSON {
      inherit ollama vulkan proxy;
      keepAlive = config.ollama.keepAlive;
      visibleDevices = config.ollama.vulkan.visibleDevices;
      httpsPort = config.ollama.proxy.httpsPort;
    }
  );
}
