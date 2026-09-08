{
  lib,
  raw ? { },
}:
let
  result =
    (lib.evalModules {
      modules = [
        { options = import ./options.nix { inherit lib; }; }
        raw
      ];
    }).config;
in
assert lib.assertMsg (
  result.ollama.vulkan.visibleDevices == null
  ||
    builtins.length result.ollama.vulkan.visibleDevices
    == builtins.length (lib.unique result.ollama.vulkan.visibleDevices)
) "Ollama Vulkan device IDs must be distinct";
builtins.deepSeq result result
