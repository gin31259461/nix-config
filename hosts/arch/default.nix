{ config, lib, ... }:
{
  imports = [ ./system.nix ];
  networking.hostName = lib.mkDefault "arch";
  deployment.username = lib.mkDefault "abnertu";
  hardware = lib.mapAttrsRecursive (_: lib.mkDefault) (import ./hardware.nix);
  programs.ai.llama = lib.mapAttrsRecursive (_: lib.mkDefault) {
    model = {
      device = "ROCm0";
    };
    profiles = {
      "thinking-general" = {
        enableThinking = true;
        temperature = 1.0;
        topP = 0.95;
        topK = 20;
        minP = 0.0;
        presencePenalty = 0.0;
        repetitionPenalty = 1.0;
      };
      "thinking-coding" = {
        enableThinking = true;
        temperature = 0.6;
        topP = 0.95;
        topK = 20;
        minP = 0.0;
        presencePenalty = 0.0;
        repetitionPenalty = 1.0;
      };
      instruct = {
        enableThinking = false;
        temperature = 0.7;
        topP = 0.8;
        topK = 20;
        minP = 0.0;
        presencePenalty = 1.5;
        repetitionPenalty = 1.0;
      };
      "preserved-thinking" = {
        preserveThinking = true;
        temperature = 0.6;
        topP = 0.95;
        topK = 20;
        minP = 0.0;
        presencePenalty = 0.0;
        repetitionPenalty = 1.0;
      };
    };
  };
  users.users = import ./users.nix { inherit config lib; };
  services.gitlabRunner.instances = lib.mapAttrs (
    _: value: lib.mapAttrsRecursive (_: lib.mkDefault) value
  ) (import ./gitlab-runners.nix);
}
