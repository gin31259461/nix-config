{
  config,
  lib,
  pkgs,
  ...
}:
let
  keyFile = "${config.xdg.dataHome}/noctalia/storage-key/master-key";
  prepare =
    "${pkgs.python3}/bin/python ${./prepare-noctalia-storage.py}"
    + " --config ${lib.escapeShellArg "${config.xdg.configHome}/noctalia"}"
    + " --state ${lib.escapeShellArg "${config.xdg.stateHome}/noctalia"}"
    + " --cache ${lib.escapeShellArg "${config.xdg.cacheHome}/noctalia"}"
    + " --key ${lib.escapeShellArg keyFile}";
in
{
  # Only the runtime filename enters the store, never the generated key.
  xdg.configFile."noctalia/storage.toml".text = ''
    [storage]
    key_source = "file"
    key_file = ${builtins.toJSON keyFile}

    [calendar]
    enabled = false
  '';

  home.activation.checkNoctaliaStorage = lib.hm.dag.entryBefore [ "checkLinkTargets" ] ''
    ${prepare} --check
  '';
  home.activation.prepareNoctaliaStorage =
    lib.hm.dag.entryBetween [ "linkGeneration" ] [ "writeBoundary" ]
      ''
        run ${prepare} --apply
      '';
}
