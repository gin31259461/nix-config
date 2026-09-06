{ lib, config }:
{
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
