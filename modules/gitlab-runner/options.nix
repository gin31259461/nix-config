{ lib }:
let
  enable = description: (lib.mkEnableOption description) // { default = true; };
in
{
  enable = enable "declared GitLab Runner instances";
  instances = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        freeformType = lib.types.attrsOf lib.types.anything;
        options.enable = enable "this Runner instance";
      }
    );
    default = { };
    description = "Runner-owned declarations; enabled instances are validated by the Runner interface.";
  };
}
