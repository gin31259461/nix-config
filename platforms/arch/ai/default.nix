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
        "--fit on"
        "--fit-target ${toString runtimeModel.fitTarget}"
        "--flash-attn on"
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
  switcher = {
    startPort = artifacts.server.port + 1000;
    includeAliasesInList = true;
    groups.default = {
      swap = true;
      exclusive = true;
      members = map (model: model.id) (builtins.attrValues artifacts.models);
    };
    models = switcherModels;
  };
  model = artifacts.model;
  prefix = artifacts.source.installPrefix + "/current";
  legacyChatTemplateKwargs =
    "{"
    + lib.concatStringsSep "," (
      lib.filter (value: value != null) [
        (
          if model.reasoningEffort or null == null then
            null
          else
            ''"reasoning_effort":${builtins.toJSON model.reasoningEffort}''
        )
        (
          if model.enableThinking or null == null then
            null
          else
            ''"enable_thinking":${builtins.toJSON model.enableThinking}''
        )
        (
          if model.preserveThinking or null == null then
            null
          else
            ''"preserve_thinking":${builtins.toJSON model.preserveThinking}''
        )
      ]
    )
    + "}";
  escapedChatTemplateKwargs = lib.replaceStrings [ "\"" ] [ "\\\"" ] (legacyChatTemplateKwargs);
  reasoningEffort = lib.optionalString (
    model.reasoningEffort or null != null
  ) " --reasoning-effort ${model.reasoningEffort}";
  switcherConfig = builtins.toJSON {
    inherit (switcher)
      startPort
      includeAliasesInList
      groups
      models
      ;
  };
  switcherUnit = ''
    [Unit]
    Description=Nix-config llama-swap model router
    After=network-online.target
    Wants=network-online.target

    [Service]
    Environment=LD_LIBRARY_PATH=${prefix}/lib:${prefix}/lib64
    ExecStart=${lib.optionalString llama "${pkgs.llama-swap}/bin/llama-swap"} --config /etc/llama-swap/config.yaml --listen 127.0.0.1:${toString artifacts.server.port}
    Restart=on-failure
    RestartSec=3

    [Install]
    WantedBy=multi-user.target
  '';
  caddyMain = ''
    {
        admin "unix//run/caddy/admin.socket"
    }

    import /etc/caddy/conf.d/*
  '';
  packageCaddy = builtins.readFile ./package-caddy.Caddyfile;
  packageCaddyWithSite =
    lib.replaceStrings
      [ "# Import additional caddy config files in /etc/caddy/conf.d/\n" ]
      [ "${legacyCaddySite}\n# Import additional caddy config files in /etc/caddy/conf.d/\n" ]
      packageCaddy;
  caddySite = ''
    :${toString artifacts.proxy.localPort} {
        bind 127.0.0.1

        @api path /health /v1/*
        handle @api {
            reverse_proxy 127.0.0.1:${toString artifacts.server.port} {
                header_up Host 127.0.0.1:${toString artifacts.server.port}
            }
        }

        respond 404
    }
  '';
  legacyCaddySite = lib.replaceStrings [ "    " ] [ "\t" ] caddySite;
  legacyPreset = ''
    version = 1

    [*]
    parallel = ${toString model.parallel}
    cont-batching = true
    jinja = true

    [${model.id}]
    model = ${model.path}
    device = ${model.device}
    ctx-size = ${toString model.contextSize}
    fit = true
    fit-target = ${toString model.fitTarget}
    fit-ctx = ${toString model.contextSize}
    flash-attn = on
    cache-type-k = ${model.cacheTypeK}
    cache-type-v = ${model.cacheTypeV}
    batch-size = ${toString model.batchSize}
    ubatch-size = ${toString model.microBatchSize}
    load-on-startup = true
  '';
  legacyDropin = ''
    [Unit]
    After=network-online.target

    [Service]
    Environment=LD_LIBRARY_PATH=${prefix}/lib:${prefix}/lib64
    ExecStart=
    ExecStart=${prefix}/bin/llama-server --models-preset /etc/llama/server/models.ini --models-max ${toString artifacts.server.modelsMax} --host ${artifacts.server.host} --port ${toString artifacts.server.port} --no-webui --temp ${builtins.toJSON model.temperature} --top-p ${builtins.toJSON model.topP} --top-k ${toString model.topK} --min-p ${builtins.toJSON model.minP} --presence-penalty ${builtins.toJSON model.presencePenalty} --repeat-penalty ${builtins.toJSON model.repetitionPenalty}${reasoningEffort} --chat-template-kwargs ${escapedChatTemplateKwargs}
    SupplementaryGroups=render video
    Restart=on-failure
    RestartSec=3
  '';
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
      }
      // switcher;
      models = artifacts.models;
      model = artifacts.model;
      localPort = artifacts.proxy.localPort;
      inherit (config.llama.proxy) httpsPort;
      generated = {
        inherit
          switcherConfig
          switcherUnit
          caddyMain
          caddySite
          packageCaddy
          packageCaddyWithSite
          legacyPreset
          legacyDropin
          ;
      };
    }
  );
}
