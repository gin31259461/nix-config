{ lib, config }:
let
  llama = config.enable && config.llama.enable;
  artifacts = import ./artifacts.nix;
  clean = value: lib.filterAttrs (_: item: item != null) value;
  modelOverrides = clean (builtins.removeAttrs config.llama.model [ "name" ]);
  modelArtifacts = lib.mapAttrs (
    _: value: value.artifact // value.runtime // { device = config.llama.model.device; }
  ) artifacts.models;
  profileDefaults = modelOverrides;
  profileInputs = config.llama.profiles // {
    default = {
      model = config.llama.model.name;
    }
    // profileDefaults
    // (config.llama.profiles.default or { });
  };
  profiles = lib.mapAttrs (
    _: profile:
    let
      selectedName = if profile.model == null then config.llama.model.name else profile.model;
      selected = artifacts.models.${selectedName};
      overrides = clean (builtins.removeAttrs profile [ "model" ]);
    in
    {
      model = selectedName;
      artifacts =
        selected.artifact
        // selected.runtime
        // overrides
        // lib.optionalAttrs ((profile.preserveThinking or null) == true) {
          enableThinking = null;
        };
    }
  ) profileInputs;
  defaultProfile = profiles.default;
  packages = import ./packages.nix;
in
{
  inherit llama;
  artifacts = artifacts // {
    model = defaultProfile.artifacts;
    models = modelArtifacts;
    inherit profiles;
  };
  aurPackages =
    lib.optionals (config.enable && config.codex.enable) packages.codex
    ++ lib.optionals (
      config.enable && config.agy.enable && config.agy.pkg.enable && config.agy.package.enable
    ) packages.agy;
  homeModule = {
    home.file = lib.optionalAttrs config.enable (
      let
        agentSkillRoot = ../../files/home/.agents/skills;
        geminiSkillRoot = ../../files/home/.gemini/config/skills;
        agentSkills =
          if config.skillsPresets.enable then
            lib.mapAttrs' (
              name: _:
              lib.nameValuePair ".agents/skills/${name}" {
                source = agentSkillRoot + "/${name}";
              }
            ) (builtins.readDir agentSkillRoot)
          else
            { };
        geminiSkills =
          if (config.agy.enable && config.agy.skills.enable) && builtins.pathExists geminiSkillRoot then
            lib.mapAttrs' (
              name: _:
              lib.nameValuePair ".gemini/config/skills/${name}" {
                source = geminiSkillRoot + "/${name}";
              }
            ) (builtins.readDir geminiSkillRoot)
          else
            { };
      in
      agentSkills // geminiSkills
    );
  };
}
