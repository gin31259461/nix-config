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
in
{
  inherit llama;
  artifacts = artifacts // {
    model = defaultProfile.artifacts;
    models = modelArtifacts;
    inherit profiles;
  };
  aurPackages = lib.optionals (config.enable && config.codex.enable) (import ./packages.nix);
  homeModule = {
    home.file = lib.optionalAttrs (config.enable && config.skillsPresets.enable) (
      let
        skillRoot = ../../files/home/.agents/skills;
      in
      lib.mapAttrs' (
        name: _:
        lib.nameValuePair ".agents/skills/${name}" {
          source = skillRoot + "/${name}";
        }
      ) (builtins.readDir skillRoot)
    );
  };
}
