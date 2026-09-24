{ platform, instances }:
let
  tomlString = builtins.toJSON;
  tomlArray = values: builtins.toJSON values;
  artifactsFor =
    instance:
    let
      account = instance.account;
      gitlab = instance.gitlab;
      runner = instance.runner;
      network = instance.network;
      uid = toString account.uid;
      runtimeDir = "/run/user/${uid}";
      configDir = "${account.home}/gitlab-runner/config";
      cacheDir = "${account.home}/gitlab-runner/cache";
      socket = "${runtimeDir}/podman/podman.sock";
      hostname = builtins.head (builtins.match "https://([^/:]+).*" gitlab.url);
      registrationTemplate =
        builtins.concatStringsSep "\n" (
          [
            "[[runners]]"
            "  name = ${tomlString runner.name}"
            "  executor = \"docker\""
            "  environment = [\"FF_NETWORK_PER_BUILD=1\"]"
            ""
            "  [runners.docker]"
            "    host = \"unix:///run/podman/podman.sock\""
            "    image = ${tomlString runner.defaultJobImage}"
            "    privileged = false"
            "    cpus = ${tomlString runner.cpus}"
            "    memory = ${tomlString runner.memory}"
            "    shm_size = ${toString runner.shmSizeBytes}"
            "    pull_policy = ${tomlString runner.pullPolicy}"
            "    volumes = [\"/cache\"]"
            "    allowed_images = ${tomlArray runner.allowedImages}"
            "    allowed_services = ${tomlArray runner.allowedServices}"
          ]
          ++ (if network.dns == null then [ ] else [ "    dns = [${tomlString network.dns}]" ])
        )
        + "\n";
      serviceUnit =
        builtins.concatStringsSep "\n" (
          [
            "[Unit]"
            "Description=GitLab Runner manager for ${runner.serviceName}"
            "Wants=network-online.target"
            "After=network-online.target podman.socket"
            "Requires=podman.socket"
            ""
            "[Service]"
            "Type=simple"
            "Environment=XDG_RUNTIME_DIR=${runtimeDir}"
            "Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=${runtimeDir}/bus"
            "ExecStartPre=-${platform.podman} rm --force ${runner.serviceName}"
            "ExecStart=${platform.podman} run \\"
            "  --rm \\"
            "  --name ${runner.serviceName} \\"
            "  --network host \\"
            "  --image-volume=ignore \\"
            "  --security-opt label=disable \\"
            "  --stop-signal SIGQUIT \\"
            "  --volume ${configDir}:/etc/gitlab-runner:rw \\"
            "  --volume ${cacheDir}:/cache:rw \\"
            "  --volume ${socket}:/run/podman/podman.sock:rw \\"
            "  --env DOCKER_HOST=unix:///run/podman/podman.sock \\"
          ]
          ++ (if network.dns == null then [ ] else [ "  --dns ${network.dns} \\" ])
          ++ [
            "  ${runner.managerImage} \\"
            "  run \\"
            "  --user=gitlab-runner \\"
            "  --working-directory=/home/gitlab-runner"
            "ExecStop=-${platform.podman} stop --time 30 ${runner.serviceName}"
            "ExecStopPost=-${platform.podman} rm --force ${runner.serviceName}"
            "Restart=always"
            "RestartSec=5"
            "TimeoutStartSec=120"
            "TimeoutStopSec=45"
            "Delegate=yes"
            ""
            "[Install]"
            "WantedBy=default.target"
          ]
        )
        + "\n";
      configPrefix = builtins.concatStringsSep "\n" [
        "concurrent = ${toString runner.concurrent}"
        "check_interval = 3"
        "shutdown_timeout = 30"
        ""
      ];
      registrationPrefix = builtins.concatStringsSep "\n" [
        "[[runners]]"
        "  name = ${tomlString runner.name}"
        "  url = ${tomlString gitlab.url}"
        "  executor = \"docker\""
        "@REGISTRATION_METADATA@"
      ];
      caLine =
        if gitlab.caCertificate == null then
          ""
        else
          "  tls-ca-file = ${tomlString "/etc/gitlab-runner/certs/${hostname}.crt"}\n";
    in
    {
      inherit registrationTemplate serviceUnit;
      configPolicy = {
        inherit configPrefix caLine;
        registrationPrefix = registrationPrefix + "\n";
      };
    };
in
builtins.mapAttrs (name: instance: instance // { artifacts = artifactsFor instance; }) instances
