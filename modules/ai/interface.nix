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
  inventory = (import ./artifacts.nix).models;
  configuredModelNames = builtins.attrNames result.llama.models;
  selectedModelNames =
    let
      enabled = lib.filter (name: result.llama.models.${name}.enable) configuredModelNames;
    in
    if configuredModelNames == [ ] then [ result.llama.model.name ] else enabled;
  effectiveModels = map (
    name:
    let
      configured = result.llama.models.${name} or { };
      clean = value: lib.filterAttrs (_: item: item != null) value;
      legacyOverrides = clean (builtins.removeAttrs result.llama.model [ "name" ]);
      modelOverrides = clean (builtins.removeAttrs configured [ "enable" ]);
      effective =
        inventory.${name}.runtime
        // (if name == result.llama.model.name then legacyOverrides else { })
        // modelOverrides;
    in
    effective
    // lib.optionalAttrs (effective.preserveThinking or null == true) {
      enableThinking = null;
    }
  ) selectedModelNames;
  effectiveDefaultModel = result.llama.model.name;
in
assert lib.assertMsg (
  result.llama.model.microBatchSize == null
  || result.llama.model.batchSize == null
  || result.llama.model.microBatchSize <= result.llama.model.batchSize
) "llama.cpp micro-batch size must not exceed batch size";
assert lib.assertMsg
  (
    let
      names = builtins.attrNames result.llama.models;
      selected = lib.filter (name: result.llama.models.${name}.enable) names;
      known = lib.all (name: builtins.hasAttr name (import ./artifacts.nix).models) names;
      selectedCount = if names == [ ] then 1 else builtins.length selected;
    in
    known
    && selectedCount > 0
    && builtins.elem result.llama.model.name selectedModelNames
    && (
      if result.llama.concurrentModels then
        selectedCount <= result.llama.maxLoadedModels
      else
        result.llama.maxLoadedModels == 1
    )
    && lib.all (
      profile:
      builtins.elem (
        if profile.model == null then effectiveDefaultModel else profile.model
      ) selectedModelNames
    ) (builtins.attrValues result.llama.profiles)
  )
  "llama.cpp selections must be known; profiles must target selected models; maxLoadedModels must match the concurrency policy";
assert lib.assertMsg (lib.all (
  model: model.microBatchSize <= model.batchSize
) effectiveModels) "llama.cpp effective model micro-batch size must not exceed batch size";
assert lib.assertMsg (
  result.llama.memoryBudgetMiB == null
  || (
    lib.all (model: model ? vramEstimateMiB) effectiveModels
    && lib.all (model: model.vramEstimateMiB != null) effectiveModels
    &&
      lib.foldl' (total: model: total + model.vramEstimateMiB) 0 effectiveModels
      <= result.llama.memoryBudgetMiB
  )
) "llama.cpp selected model VRAM estimates must be declared and fit within memoryBudgetMiB";
assert lib.assertMsg (lib.all
  (profile: !((profile.enableThinking or null) == true && (profile.preserveThinking or null) == true))
  (builtins.attrValues result.llama.profiles)
) "llama.cpp profiles must choose enable-thinking or preserve-thinking, not both";
assert lib.assertMsg (lib.all
  (
    profile:
    let
      name = if profile.model == null then effectiveDefaultModel else profile.model;
      model = builtins.elemAt effectiveModels (
        lib.lists.findFirstIndex (candidate: candidate == name) 0 selectedModelNames
      );
      enableThinking =
        if profile.enableThinking == null then model.enableThinking or null else profile.enableThinking;
      preserveThinking =
        if profile.preserveThinking == null then
          model.preserveThinking or null
        else
          profile.preserveThinking;
    in
    !(enableThinking == true && preserveThinking == true) || profile.preserveThinking == true
  )
  (builtins.attrValues result.llama.profiles)
) "llama.cpp effective profiles must not enable and preserve thinking together";
assert lib.assertMsg (
  !(
    (result.llama.model.enableThinking or null) == true
    && (result.llama.model.preserveThinking or null) == true
  )
  && lib.all (
    model: !((model.enableThinking or null) == true && (model.preserveThinking or null) == true)
  ) (builtins.attrValues result.llama.models)
) "llama.cpp runtime settings must choose enable-thinking or preserve-thinking, not both";
builtins.deepSeq result result
