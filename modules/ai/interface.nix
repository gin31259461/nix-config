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
builtins.deepSeq result result
