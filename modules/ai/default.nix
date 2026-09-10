{ lib, config }:
let
  llama = config.enable && config.llama.enable;
  artifacts = import ./artifacts.nix;
  selected = artifacts.models.${config.llama.model.name};
  overrides = lib.filterAttrs (_: value: value != null) (
    builtins.removeAttrs config.llama.model [ "name" ]
  );
in
{
  inherit llama;
  artifacts = artifacts // {
    model = selected.artifact // selected.runtime // overrides;
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
