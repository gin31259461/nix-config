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
  result.llama.model.microBatchSize == null
  || result.llama.model.batchSize == null
  || result.llama.model.microBatchSize <= result.llama.model.batchSize
) "llama.cpp micro-batch size must not exceed batch size";
assert lib.assertMsg (lib.all
  (profile: !((profile.enableThinking or null) == true && (profile.preserveThinking or null) == true))
  (builtins.attrValues result.llama.profiles)
) "llama.cpp profiles must choose enable-thinking or preserve-thinking, not both";
builtins.deepSeq result result
