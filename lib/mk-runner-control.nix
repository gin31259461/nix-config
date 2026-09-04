{
  pkgs,
  instances,
  platform ? {
    podman = "${pkgs.podman}/bin/podman";
    ip = "${pkgs.iproute2}/bin/ip";
  },
}:
let
  config = pkgs.writeText "gitlab-runner-instances.json" (
    builtins.toJSON { inherit instances platform; }
  );
in
pkgs.writeShellApplication {
  name = "runnerctl";
  runtimeInputs = with pkgs; [
    coreutils
    curl
    iproute2
    python3
    shadow
    systemd
    util-linux
  ];
  text = ''
    exec python3 ${../modules/gitlab-runner/runnerctl.py} --config ${config} "$@"
  '';
}
