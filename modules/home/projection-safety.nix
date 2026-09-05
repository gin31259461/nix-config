{ config, lib, ... }:
{
  home.activation.checkExternalConfigTargets = lib.hm.dag.entryBefore [ "checkLinkTargets" ] ''
    (
      home_dir=${lib.escapeShellArg config.home.homeDirectory}
      ${builtins.readFile ./check-projection.sh}
    )
  '';
}
