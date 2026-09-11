{
  lib,
  pkgs,
  artifacts,
}:
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
    readonly model_repositories=(${
      lib.escapeShellArgs (map (model: model.repository) (builtins.attrValues artifacts.models))
    })
    readonly model_revisions=(${
      lib.escapeShellArgs (map (model: model.revision) (builtins.attrValues artifacts.models))
    })
    readonly model_files=(${
      lib.escapeShellArgs (map (model: model.file) (builtins.attrValues artifacts.models))
    })
    readonly model_paths=(${
      lib.escapeShellArgs (map (model: model.path) (builtins.attrValues artifacts.models))
    })
    readonly model_sha256s=(${
      lib.escapeShellArgs (map (model: model.sha256) (builtins.attrValues artifacts.models))
    })
  ''
  + builtins.readFile ./prepare.sh;
}
