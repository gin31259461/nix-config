{
  pkgs,
  config,
  artifacts,
  hardware,
  tailscale,
}:
let
  llama = config.enable && config.llama.enable;
  proxy = llama && config.llama.proxy.enable && tailscale;
in
{
  inherit llama proxy;
  manifest = pkgs.writeText "arch-ai.json" (
    builtins.toJSON {
      inherit llama proxy;
      inherit (artifacts) source server;
      model = artifacts.model;
      localPort = artifacts.proxy.localPort;
      inherit (config.llama.proxy) httpsPort;
    }
  );
}
