{ lib }:
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
}
