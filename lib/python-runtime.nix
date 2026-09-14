{
  lib,
  pkgs,
  inputs,
}:
let
  workspace = inputs.uv2nix.lib.workspace.loadWorkspace {
    workspaceRoot = ../.;
  };
  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };
  python = pkgs.python312;
  pythonBase = pkgs.callPackage inputs.pyproject-nix.build.packages {
    inherit python;
  };
  pythonSet = pythonBase.overrideScope (
    lib.composeManyExtensions [
      inputs.pyproject-build-systems.overlays.default
      overlay
    ]
  );
  runtime = pythonSet.mkVirtualEnv "nix-config-python" workspace.deps.default;
in
{
  inherit
    python
    pythonSet
    runtime
    workspace
    ;
}
