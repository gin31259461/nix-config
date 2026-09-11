{
  lib,
  pkgs,
  config,
  artifacts,
  hardware,
  tailscale,
}:
let
  llama = config.enable && config.llama.enable;
  proxy = llama && config.llama.proxy.enable && tailscale;
  modelProfiles =
    modelName: lib.filterAttrs (_: profile: profile.model == modelName) artifacts.profiles;
  profileAlias =
    name: profile:
    if name == "default" then profile.artifacts.id else "${profile.artifacts.id}:${name}";
  chatTemplateKwargs =
    profile:
    lib.filterAttrs (_: value: value != null) {
      reasoning_effort = profile.artifacts.reasoningEffort or null;
      enable_thinking = profile.artifacts.enableThinking or null;
      preserve_thinking = profile.artifacts.preserveThinking or null;
    };
  requestParams =
    profile:
    {
      temperature = profile.artifacts.temperature;
      top_p = profile.artifacts.topP;
      top_k = profile.artifacts.topK;
      min_p = profile.artifacts.minP;
      presence_penalty = profile.artifacts.presencePenalty;
      repetition_penalty = profile.artifacts.repetitionPenalty;
    }
    // lib.optionalAttrs (chatTemplateKwargs profile != { }) {
      chat_template_kwargs = chatTemplateKwargs profile;
    };
  switcherModels = lib.mapAttrs' (
    modelName: model:
    let
      profiles = modelProfiles modelName;
      runtimeModel = model // profiles.default.artifacts;
      aliases = lib.filter (alias: alias != model.id) (lib.mapAttrsToList profileAlias profiles);
      paramsById = lib.mapAttrs' (
        name: profile: lib.nameValuePair (profileAlias name profile) (requestParams profile)
      ) profiles;
      command = lib.concatStringsSep " " [
        "${artifacts.source.installPrefix}/current/bin/llama-server"
        "--model ${lib.escapeShellArg runtimeModel.path}"
        "--host 127.0.0.1"
        "--port \${PORT}"
        "--no-webui"
        "--ctx-size ${toString runtimeModel.contextSize}"
        "--fit"
        "--fit-target ${toString runtimeModel.fitTarget}"
        "--flash-attn"
        "--cache-type-k ${runtimeModel.cacheTypeK}"
        "--cache-type-v ${runtimeModel.cacheTypeV}"
        "--batch-size ${toString runtimeModel.batchSize}"
        "--ubatch-size ${toString runtimeModel.microBatchSize}"
        "--parallel ${toString runtimeModel.parallel}"
        "--device ${runtimeModel.device}"
      ];
    in
    lib.nameValuePair model.id {
      cmd = command;
      proxy = "http://127.0.0.1:\${PORT}";
      checkEndpoint = "/health";
      inherit aliases;
      filters.setParamsByID = paramsById;
    }
  ) artifacts.models;
in
{
  inherit llama proxy;
  manifest = pkgs.writeText "arch-ai.json" (
    builtins.toJSON {
      inherit llama proxy;
      inherit (artifacts) source server profiles;
      switcher = {
        binary = lib.optionalString llama "${pkgs.llama-swap}/bin/llama-swap";
        listen = "127.0.0.1:${toString artifacts.server.port}";
        startPort = artifacts.server.port + 1000;
        includeAliasesInList = true;
        groups.default = {
          swap = true;
          exclusive = true;
          members = map (model: model.id) (builtins.attrValues artifacts.models);
        };
        models = switcherModels;
      };
      models = artifacts.models;
      model = artifacts.model;
      localPort = artifacts.proxy.localPort;
      inherit (config.llama.proxy) httpsPort;
    }
  );
}
