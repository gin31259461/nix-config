{ pkgs, artifacts }:
pkgs.writeShellApplication {
  name = "llama-prepare";
  runtimeInputs = with pkgs; [
    cmake
    coreutils
    curl
    git
    gnused
    ninja
    util-linux
  ];
  text = ''
    readonly source_repository=${pkgs.lib.escapeShellArg artifacts.source.repository}
    readonly source_revision=${pkgs.lib.escapeShellArg artifacts.source.revision}
    readonly grammar_threshold=${toString artifacts.source.grammarRepetitionThreshold}
    readonly install_prefix=${pkgs.lib.escapeShellArg artifacts.source.installPrefix}
    readonly model_repository=${pkgs.lib.escapeShellArg artifacts.model.repository}
    readonly model_revision=${pkgs.lib.escapeShellArg artifacts.model.revision}
    readonly model_file=${pkgs.lib.escapeShellArg artifacts.model.file}
    readonly model_path=${pkgs.lib.escapeShellArg artifacts.model.path}
    readonly model_sha256=${pkgs.lib.escapeShellArg artifacts.model.sha256}
  ''
  + builtins.readFile ./prepare.sh;
}
