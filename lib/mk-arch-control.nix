{
  lib,
  pkgs,
  host,
}:
let
  packages = host.systemPackages;
  files = ../platforms/arch/files;
  lizardbytePackages = map (package: "lizardbyte/${package}") packages.lizardbyte;
  deploymentUser = host.users.${host.deployment.username};
  requiredGroups = lib.unique (
    (deploymentUser.groups or [ ]) ++ lib.optional deploymentUser.admin "wheel"
  );
in
pkgs.writeShellApplication {
  name = "arch-switch";
  runtimeInputs = with pkgs; [
    coreutils
    gawk
    gnugrep
    gnused
  ];
  text = ''
    usage() {
      printf 'usage: arch-switch [--check | --update]\n'
    }

    check_only=0
    update_system=0
    while (( $# )); do
      case $1 in
        --check)
          check_only=1
          ;;
        --update)
          update_system=1
          ;;
        --help)
          usage
          exit 0
          ;;
        *)
          usage >&2
          exit 2
          ;;
      esac
      shift
    done
    if (( check_only && update_system )); then
      usage >&2
      exit 2
    fi

    if [[ ! -e /etc/arch-release ]]; then
      printf 'arch-switch only supports Arch Linux\n' >&2
      exit 1
    fi
    if [[ $EUID -eq 0 ]]; then
      printf 'run arch-switch as the login user, not root\n' >&2
      exit 1
    fi
    for command in \
      /usr/bin/id \
      /usr/bin/install \
      /usr/bin/pacman \
      /usr/bin/pacman-conf \
      /usr/bin/sudo \
      /usr/bin/systemctl \
      /usr/bin/tee \
      /usr/bin/yay; do
      if [[ ! -x $command ]]; then
        printf 'required command is missing: %s\n' "$command" >&2
        exit 1
      fi
    done
    login_user=$(/usr/bin/id --user --name)
    expected_user=${lib.escapeShellArg host.deployment.username}
    if [[ $login_user != "$expected_user" ]]; then
      printf 'arch-switch must run as %s, not %s\n' "$expected_user" "$login_user" >&2
      exit 1
    fi
    if ! /usr/bin/id -nG "$login_user" | tr ' ' '\n' | grep -Fxq wheel; then
      printf 'deployment user is not in required administrator group: wheel\n' >&2
      printf 'grant wheel membership through the Arch bootstrap path, then retry\n' >&2
      exit 1
    fi

    pacman_packages=(${lib.escapeShellArgs packages.pacman})
    lizardbyte_package_names=(${lib.escapeShellArgs packages.lizardbyte})
    lizardbyte_packages=(${lib.escapeShellArgs lizardbytePackages})
    aur_packages=(${lib.escapeShellArgs packages.aur})
    work_dir="$(mktemp -d)"
    package_check="$work_dir/package-check"
    lizardbyte_database="$work_dir/lizardbyte.db"
    lizardbyte_database_files="$work_dir/lizardbyte-files"
    trap 'rm -rf -- "$work_dir"' EXIT

    if ! /usr/bin/pacman --sync --print --needed -- \
      "''${pacman_packages[@]}" > /dev/null 2> "$package_check"; then
      cat "$package_check" >&2
      printf 'Arch package inventory did not resolve\n' >&2
      exit 1
    fi
    lizardbyte_server="$(
      /usr/bin/pacman-conf \
        --config ${files}/pacman-lizardbyte.conf \
        --repo lizardbyte \
        Server
    )"
    ${pkgs.curl}/bin/curl \
      --fail \
      --location \
      --show-error \
      --silent \
      --output "$lizardbyte_database" \
      "$lizardbyte_server/lizardbyte.db"
    ${pkgs.libarchive}/bin/bsdtar -tf "$lizardbyte_database" \
      > "$lizardbyte_database_files"
    for package in "''${lizardbyte_package_names[@]}"; do
      if ! grep -Eq "^$package-[^/]+/desc$" "$lizardbyte_database_files"; then
        printf 'LizardByte package did not resolve: %s\n' "$package" >&2
        exit 1
      fi
    done
    if ! /usr/bin/yay --sync --info -- \
      "''${aur_packages[@]}" > /dev/null 2> "$package_check"; then
      cat "$package_check" >&2
      printf 'AUR package inventory did not resolve\n' >&2
      exit 1
    fi
    if (( check_only )); then
      printf 'Arch, LizardByte, and AUR package inventories resolve\n'
      exit 0
    fi

    missing_packages=()
    for package in \
      "''${pacman_packages[@]}" \
      "''${lizardbyte_package_names[@]}" \
      "''${aur_packages[@]}"; do
      if ! /usr/bin/pacman --query -- "$package" > /dev/null 2>&1; then
        missing_packages+=("$package")
      fi
    done
    if (( ! update_system && ''${#missing_packages[@]} )); then
      printf 'declared Arch packages are missing; rerun with --update to install them safely:\n' >&2
      printf '  %s\n' "''${missing_packages[@]}" >&2
      exit 3
    fi

    running_kernel="$(uname -r)"
    if [[ ! -d /usr/lib/modules/$running_kernel ]]; then
      printf \
        'installed kernel modules do not match running kernel %s; reboot, then rerun the deployment\n' \
        "$running_kernel" >&2
      exit 75
    fi

    repo_file=/etc/pacman.d/nix-config-lizardbyte.conf
    repo_include="Include = $repo_file"
    if ! grep -Fxq "$repo_include" /etc/pacman.conf \
      && /usr/bin/pacman-conf --repo lizardbyte Server > /dev/null 2>&1; then
      printf 'an unmanaged [lizardbyte] repository already exists in pacman.conf\n' >&2
      exit 1
    fi

    /usr/bin/sudo -v
    /usr/bin/sudo /usr/bin/install -Dm0644 \
      ${files}/pacman-lizardbyte.conf \
      "$repo_file"
    if ! grep -Fxq "$repo_include" /etc/pacman.conf; then
      printf '\n%s\n' "$repo_include" \
        | /usr/bin/sudo /usr/bin/tee -a /etc/pacman.conf > /dev/null
    fi
    if [[ $(/usr/bin/pacman-conf --repo lizardbyte Server) != "$lizardbyte_server" ]]; then
      printf 'managed [lizardbyte] repository did not load as expected\n' >&2
      exit 1
    fi

    if (( update_system )); then
      /usr/bin/sudo /usr/bin/pacman \
        --sync \
        --refresh \
        --sysupgrade \
        --needed \
        --noconfirm \
        -- \
        "''${pacman_packages[@]}" \
        "''${lizardbyte_packages[@]}"
      if [[ ! -d /usr/lib/modules/$running_kernel ]]; then
        printf \
          'the kernel was upgraded from %s; reboot, then rerun the deployment\n' \
          "$running_kernel" >&2
        exit 75
      fi
      /usr/bin/yay --sync --needed --noconfirm -- "''${aur_packages[@]}"
    fi

    /usr/bin/sudo /usr/bin/install -Dm0644 \
      ${files}/NetworkManager-main.conf \
      /etc/NetworkManager/conf.d/main.conf
    /usr/bin/sudo /usr/bin/install -Dm0644 \
      ${files}/NetworkManager-tailscale.conf \
      /etc/NetworkManager/conf.d/99-tailscale.conf
    /usr/bin/sudo /usr/bin/install -Dm0644 \
      ${files}/podman-modules.conf \
      /etc/modules-load.d/nix-config-podman.conf
    /usr/bin/sudo /usr/bin/install -Dm0644 \
      ${files}/sysctl.conf \
      /etc/sysctl.d/99-nix-config.conf

    autologin_file="$work_dir/tty1-autologin.conf"
    mkinitcpio_file="$work_dir/mkinitcpio.conf"
    sed "s/@USER@/$login_user/g" ${files}/tty1-autologin.conf > "$autologin_file"
    /usr/bin/sudo /usr/bin/install -Dm0644 "$autologin_file" \
      /etc/systemd/system/getty@tty1.service.d/override.conf

    if /usr/bin/lsmod | awk '{print tolower($1)}' | grep -Fxq amdgpu; then
      awk '
        BEGIN { replaced = 0 }
        /^[[:space:]]*MODULES=/ {
          print "MODULES=(usbhid xhci_pci amdgpu)"
          replaced = 1
          next
        }
        { print }
        END {
          if (!replaced) print "MODULES=(usbhid xhci_pci amdgpu)"
        }
      ' /etc/mkinitcpio.conf > "$mkinitcpio_file"
      /usr/bin/sudo /usr/bin/install -m0644 "$mkinitcpio_file" /etc/mkinitcpio.conf
      /usr/bin/sudo /usr/bin/mkinitcpio -P
    fi

    required_groups=(${lib.escapeShellArgs requiredGroups})
    for group in "''${required_groups[@]}"; do
      if ! /usr/bin/id -nG "$login_user" | tr ' ' '\n' | grep -Fxq "$group"; then
        /usr/bin/sudo /usr/bin/gpasswd --add "$login_user" "$group"
      fi
    done

    /usr/bin/sudo /usr/bin/systemctl enable --now \
      NetworkManager.service \
      bluetooth.service \
      power-profiles-daemon.service \
      tailscaled.service
    /usr/bin/sudo /usr/bin/systemctl try-restart NetworkManager.service
    /usr/bin/sudo /usr/bin/sysctl --system

    /usr/bin/systemctl --user enable openrazer-daemon.service

    sunshine="$(readlink -f /usr/bin/sunshine)"
    if ! /usr/bin/getcap "$sunshine" | grep -Fq cap_sys_admin; then
      /usr/bin/sudo /usr/bin/setcap cap_sys_admin+p "$sunshine"
    fi
    /usr/bin/systemctl --user enable app-dev.lizardbyte.app.Sunshine.service

    printf 'Arch system configuration converged; log out once if group membership changed.\n'
  '';
}
