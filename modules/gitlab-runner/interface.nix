{
  lib,
  rawInstances,
}:
let
  inherit (builtins)
    attrNames
    elemAt
    isAttrs
    isInt
    isList
    isPath
    isString
    length
    match
    ;
  inherit (lib)
    all
    any
    assertMsg
    hasSuffix
    mapAttrs
    subtractLists
    unique
    ;

  managerImage = "docker.io/gitlab/gitlab-runner:v18.10.1";
  validationImage = "docker.io/curlimages/curl:8.12.1";
  subordinateIdCount = 65536;

  assertFields =
    context: allowed: value:
    let
      unknown = subtractLists allowed (attrNames value);
    in
    assert assertMsg (isAttrs value) "${context} must be an attribute set";
    assert assertMsg (
      unknown == [ ]
    ) "${context} has unknown fields: ${builtins.concatStringsSep ", " unknown}";
    value;

  allStrings = values: isList values && all isString values;
  httpsHost =
    value:
    let
      parsed = if isString value then match "https://([^/:]+)(:[0-9]+)?(/.*)?" value else null;
    in
    if parsed == null then null else elemAt parsed 0;
  fixedImage =
    value:
    isString value
    &&
      match "[a-z0-9.-]+(:[0-9]+)?/[A-Za-z0-9._/-]+(:[A-Za-z0-9._-]+|@sha256:[a-f0-9]{64})" value != null
    && !hasSuffix ":latest" value;
  imagePattern =
    value:
    isString value
    &&
      match "[a-z0-9.*?-]+(:[0-9*]+)?/[A-Za-z0-9._/*?-]+(:[A-Za-z0-9._*?-]+|@sha256:[a-f0-9*?]+)" value
      != null
    && !hasSuffix ":latest" value;
  globToRegex =
    value:
    builtins.replaceStrings
      [
        "."
        "+"
        "("
        ")"
        "["
        "]"
        "{"
        "}"
        "^"
        "$"
        "|"
        "*"
        "?"
      ]
      [
        "\\."
        "\\+"
        "\\("
        "\\)"
        "\\["
        "\\]"
        "\\{"
        "\\}"
        "\\^"
        "\\$"
        "\\|"
        ".*"
        "."
      ]
      value;
  matchesImagePattern = image: pattern: match (globToRegex pattern) image != null;
  positiveCpu =
    value:
    isString value
    && (match "[1-9][0-9]*(\\.[0-9]+)?" value != null || match "0\\.[0-9]*[1-9][0-9]*" value != null);
  positiveMemory = value: isString value && match "[1-9][0-9]*([kKmMgGtT][bB]?)?" value != null;
  rangesOverlap =
    left: right:
    left.start <= right.start + right.count - 1 && right.start <= left.start + left.count - 1;

  normalize =
    instanceName: raw:
    let
      instance = assertFields "GitLab Runner instance ${instanceName}" [
        "uid"
        "subordinateIdStart"
        "gitlab"
        "runner"
        "network"
      ] raw;
      gitlab = assertFields "GitLab Runner instance ${instanceName}.gitlab" [
        "url"
        "healthUrl"
        "caCertificate"
      ] instance.gitlab;
      runner = assertFields "GitLab Runner instance ${instanceName}.runner" [
        "name"
        "cpus"
        "memory"
        "shmSizeBytes"
        "defaultJobImage"
        "allowedImages"
        "allowedServices"
      ] instance.runner;
      network = assertFields "GitLab Runner instance ${instanceName}.network" [
        "requiredInterface"
        "dns"
      ] instance.network;
      user = "gitlab-runner-${instanceName}";
      urlHost = httpsHost gitlab.url;
      healthHost = httpsHost gitlab.healthUrl;
      subordinateIdEnd = instance.subordinateIdStart + subordinateIdCount - 1;
      caCertificate = gitlab.caCertificate or null;
      requiredInterface = network.requiredInterface or null;
      dns = network.dns or null;
    in
    assert assertMsg (
      match "[a-z][a-z0-9-]{0,17}" instanceName != null
    ) "invalid GitLab Runner instance name: ${instanceName}";
    assert assertMsg (
      isInt instance.uid && instance.uid > 0
    ) "GitLab Runner instance ${instanceName}.uid must be a positive integer";
    assert assertMsg (
      isInt instance.subordinateIdStart && instance.subordinateIdStart > 0
    ) "GitLab Runner instance ${instanceName}.subordinateIdStart must be a positive integer";
    assert assertMsg (
      subordinateIdEnd <= 4294967294
    ) "GitLab Runner instance ${instanceName} subordinate IDs exceed the supported range";
    assert assertMsg (
      urlHost != null
    ) "GitLab Runner instance ${instanceName}.gitlab.url must be HTTPS";
    assert assertMsg (
      healthHost == urlHost
    ) "GitLab Runner instance ${instanceName} GitLab URLs must use the same hostname";
    assert assertMsg (
      caCertificate == null || isPath caCertificate
    ) "GitLab Runner instance ${instanceName}.gitlab.caCertificate must be a Nix path or null";
    assert assertMsg (
      isString runner.name && runner.name != ""
    ) "GitLab Runner instance ${instanceName}.runner.name must not be empty";
    assert assertMsg (positiveCpu runner.cpus)
      "GitLab Runner instance ${instanceName}.runner.cpus must be positive";
    assert assertMsg (positiveMemory runner.memory)
      "GitLab Runner instance ${instanceName}.runner.memory must be a positive size";
    assert assertMsg (
      isInt runner.shmSizeBytes && runner.shmSizeBytes > 0
    ) "GitLab Runner instance ${instanceName}.runner.shmSizeBytes must be positive";
    assert assertMsg (fixedImage runner.defaultJobImage)
      "GitLab Runner instance ${instanceName}.runner.defaultJobImage must be registry-qualified and pinned";
    assert assertMsg (
      runner.allowedImages != [ ]
      && allStrings runner.allowedImages
      && all imagePattern runner.allowedImages
    ) "GitLab Runner instance ${instanceName}.runner.allowedImages must contain qualified patterns";
    assert assertMsg (any (matchesImagePattern runner.defaultJobImage) runner.allowedImages)
      "GitLab Runner instance ${instanceName}.runner.defaultJobImage must match allowedImages";
    assert assertMsg (
      allStrings runner.allowedServices && all imagePattern runner.allowedServices
    ) "GitLab Runner instance ${instanceName}.runner.allowedServices must contain qualified patterns";
    assert assertMsg (
      requiredInterface == null
      || (isString requiredInterface && match "[A-Za-z0-9_.:-]+" requiredInterface != null)
    ) "GitLab Runner instance ${instanceName}.network.requiredInterface is invalid";
    assert assertMsg (
      dns == null || (isString dns && match "[0-9A-Fa-f:.]+" dns != null)
    ) "GitLab Runner instance ${instanceName}.network.dns must be an IP address";
    {
      account = {
        inherit user;
        uid = instance.uid;
        home = "/home/${user}";
        subUid = {
          start = instance.subordinateIdStart;
          count = subordinateIdCount;
        };
        subGid = {
          start = instance.subordinateIdStart;
          count = subordinateIdCount;
        };
      };
      gitlab = {
        inherit (gitlab) url healthUrl;
        inherit caCertificate;
      };
      runner = {
        inherit (runner)
          name
          cpus
          memory
          shmSizeBytes
          defaultJobImage
          allowedImages
          allowedServices
          ;
        serviceName = user;
        inherit managerImage;
        concurrent = 1;
        pullPolicy = "if-not-present";
      };
      network = {
        inherit requiredInterface dns;
      };
      validation.image = validationImage;
    };

  instances = mapAttrs normalize rawInstances;
  values = builtins.attrValues instances;
  uids = map (instance: instance.account.uid) values;
  rangesDoNotOverlap = all (
    left:
    all (
      right:
      left.account.user == right.account.user || !rangesOverlap left.account.subUid right.account.subUid
    ) values
  ) values;
in
assert assertMsg (instances != { }) "at least one GitLab Runner instance is required";
assert assertMsg (length uids == length (unique uids)) "GitLab Runner account UIDs must be unique";
assert assertMsg rangesDoNotOverlap "GitLab Runner subordinate ID ranges overlap";
instances
