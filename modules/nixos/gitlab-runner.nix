{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (lib)
    attrValues
    concatMap
    mapAttrs'
    mkEnableOption
    mkIf
    mkOption
    nameValuePair
    types
    ;
  cfg = config.orbit.gitlabRunner;

  idRangeType = types.submodule {
    options = {
      start = mkOption {
        type = types.ints.positive;
        description = "First subordinate ID in the allocation.";
      };
      count = mkOption {
        type = types.ints.positive;
        default = 65536;
        description = "Number of subordinate IDs in the allocation.";
      };
    };
  };

  instanceType = types.submodule {
    options = {
      account = {
        user = mkOption { type = types.str; };
        uid = mkOption { type = types.ints.positive; };
        home = mkOption { type = types.str; };
        subUid = mkOption { type = idRangeType; };
        subGid = mkOption { type = idRangeType; };
      };
      gitlab = {
        url = mkOption { type = types.str; };
        healthUrl = mkOption { type = types.str; };
      };
      runner = {
        name = mkOption { type = types.str; };
        serviceName = mkOption { type = types.str; };
        managerImage = mkOption { type = types.str; };
        tags = mkOption {
          type = types.listOf types.str;
          default = [ ];
        };
        concurrent = mkOption {
          type = types.ints.positive;
          default = 1;
        };
        cpus = mkOption { type = types.str; };
        memory = mkOption { type = types.str; };
        shmSizeBytes = mkOption { type = types.ints.positive; };
        pullPolicy = mkOption {
          type = types.enum [
            "always"
            "if-not-present"
            "never"
          ];
          default = "if-not-present";
        };
        defaultJobImage = mkOption { type = types.str; };
        allowedImages = mkOption { type = types.listOf types.str; };
        allowedServices = mkOption {
          type = types.listOf types.str;
          default = [ ];
        };
      };
      network = {
        requiredInterface = mkOption {
          type = types.nullOr types.str;
          default = null;
          description = ''
            Interface that must exist and have its UP flag before the Runner is
            reconciled or verified. This does not imply forced routing.
          '';
        };
        dns = mkOption {
          type = types.nullOr types.str;
          default = null;
        };
      };
      validation.image = mkOption { type = types.str; };
    };
  };

  instances = attrValues cfg.instances;
  users = map (instance: instance.account.user) instances;
  uids = map (instance: instance.account.uid) instances;
  services = map (instance: instance.runner.serviceName) instances;
  rangesOverlap =
    left: right:
    left.start <= right.start + right.count - 1 && right.start <= left.start + left.count - 1;
  noRangeOverlap =
    rangeName:
    lib.all (
      left:
      lib.all (
        right:
        left.account.user == right.account.user
        || !(rangesOverlap left.account.${rangeName} right.account.${rangeName})
      ) instances
    ) instances;

  runnerctl = import ../../lib/mk-runner-control.nix {
    inherit pkgs;
    instances = cfg.instances;
  };
in
{
  options.orbit.gitlabRunner = {
    enable = mkEnableOption "dedicated rootless Podman GitLab Runner instances";
    instances = mkOption {
      type = types.attrsOf instanceType;
      default = { };
      description = "GitLab Runner instances owned by this module.";
    };
  };

  config = mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.instances != { };
        message = "orbit.gitlabRunner requires at least one instance";
      }
      {
        assertion = builtins.length users == builtins.length (lib.unique users);
        message = "GitLab Runner accounts must be unique";
      }
      {
        assertion = builtins.length uids == builtins.length (lib.unique uids);
        message = "GitLab Runner UIDs must be unique";
      }
      {
        assertion = builtins.length services == builtins.length (lib.unique services);
        message = "GitLab Runner service names must be unique";
      }
      {
        assertion = noRangeOverlap "subUid";
        message = "GitLab Runner subordinate UID ranges overlap";
      }
      {
        assertion = noRangeOverlap "subGid";
        message = "GitLab Runner subordinate GID ranges overlap";
      }
    ];

    boot.kernelModules = [
      "bridge"
      "br_netfilter"
      "veth"
    ];
    boot.kernel.sysctl = {
      "net.ipv4.ip_forward" = 1;
      "net.bridge.bridge-nf-call-iptables" = 1;
    };

    environment.systemPackages = [ runnerctl ];
    virtualisation.podman.enable = true;

    users.groups = mapAttrs' (_: instance: nameValuePair instance.account.user { }) cfg.instances;
    users.users = mapAttrs' (
      _: instance:
      nameValuePair instance.account.user {
        uid = instance.account.uid;
        group = instance.account.user;
        home = instance.account.home;
        createHome = true;
        isSystemUser = true;
        shell = pkgs.bashInteractive;
        subUidRanges = [
          {
            startUid = instance.account.subUid.start;
            count = instance.account.subUid.count;
          }
        ];
        subGidRanges = [
          {
            startGid = instance.account.subGid.start;
            count = instance.account.subGid.count;
          }
        ];
      }
    ) cfg.instances;

    systemd.tmpfiles.rules = concatMap (instance: [
      "d ${instance.account.home}/gitlab-runner 0700 ${instance.account.user} ${instance.account.user} -"
      "d ${instance.account.home}/gitlab-runner/config 0700 ${instance.account.user} ${instance.account.user} -"
      "d ${instance.account.home}/gitlab-runner/cache 0700 ${instance.account.user} ${instance.account.user} -"
      "d ${instance.account.home}/.config/systemd/user 0700 ${instance.account.user} ${instance.account.user} -"
    ]) instances;
  };
}
