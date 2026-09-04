{
  description = "Personal Arch Linux configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

    home-manager = {
      url = "github:nix-community/home-manager/release-26.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    neovim-config = {
      url = "github:Orbit-Lua/orbitvim";
      flake = false;
    };

    hypr-config = {
      url = "github:Orbit-Lua/hypr";
      flake = false;
    };
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      ...
    }:
    let
      inherit (nixpkgs) lib;
      mkHomeConfiguration = import ./lib/mk-home-configuration.nix { inherit inputs; };
      archHost = import ./hosts/arch;
      archHomes = lib.mapAttrs' (
        username: user:
        lib.nameValuePair "${username}@${archHost.name}" (mkHomeConfiguration {
          inherit username user;
          hostName = archHost.name;
          platform = archHost.platform;
          system = archHost.system;
        })
      ) archHost.users;
      deployment = archHost.deployment;
      deploymentUser =
        archHost.users.${deployment.username} or (throw "unknown deployment user: ${deployment.username}");
      deploymentName = "${archHost.name}-${deployment.profile}";
      homeConfigurationName = "${deployment.username}@${archHost.name}";
      system = archHost.system;
      pkgs = nixpkgs.legacyPackages.${system};
      runnerInstances = import ./modules/gitlab-runner/interface.nix {
        inherit lib;
        rawInstances = archHost.gitlabRunners;
      };
      runnerInterfaceTests = import ./modules/gitlab-runner/interface_test.nix {
        inherit lib;
        rawInstances = archHost.gitlabRunners;
      };
      runnerArch = import ./modules/gitlab-runner/arch.nix {
        inherit lib;
        packageInventory = archHost.systemPackages.pacman;
      };
      runnerPlatform = runnerArch.platform;
      runnerctl = import ./modules/gitlab-runner/package.nix {
        inherit pkgs;
        instances = runnerInstances;
        platform = runnerPlatform;
      };
      arch-switch = import ./lib/mk-arch-control.nix {
        inherit lib pkgs;
        host = archHost;
      };
      home-switch = pkgs.writeShellApplication {
        name = "home-switch";
        runtimeInputs = [ inputs.home-manager.packages.${system}.home-manager ];
        text = ''
          exec home-manager switch --flake '${self}#${homeConfigurationName}' "$@"
        '';
      };
      archDeployment = pkgs.writeShellApplication {
        name = deploymentName;
        text = ''
          arch_switch_args=()
          if [[ ''${1-} == --update ]]; then
            arch_switch_args+=(--update)
            shift
          elif [[ ''${1-} == --help ]]; then
            printf 'usage: ${deploymentName} [--update] [HOME_MANAGER_ARGUMENTS...]\n'
            exit 0
          fi

          if [[ ! -x ${archHomes.${homeConfigurationName}.activationPackage}/activate ]]; then
            printf 'Home Manager activation package is unavailable\n' >&2
            exit 1
          fi

          ${arch-switch}/bin/arch-switch "''${arch_switch_args[@]}"
          exec ${home-switch}/bin/home-switch "$@"
        '';
      };
    in
    assert lib.assertMsg (builtins.elem deployment.profile deploymentUser.profiles)
      "deployment profile ${deployment.profile} is not selected by ${deployment.username}";
    assert lib.assertMsg deploymentUser.admin
      "deployment user ${deployment.username} must be an administrator";
    {
      homeConfigurations = archHomes;

      checks.${system} = {
        arch-home = archHomes.${homeConfigurationName}.activationPackage;
        arch-switch-interface = pkgs.runCommand "arch-switch-interface-check" { } ''
          ${arch-switch}/bin/arch-switch --help \
            | ${pkgs.gnugrep}/bin/grep -Fxq 'usage: arch-switch [--check | --update]'
          ${pkgs.gnugrep}/bin/grep -Fq \
            'deployment user is not in required administrator group: wheel' \
            ${arch-switch}/bin/arch-switch
          ${pkgs.gnugrep}/bin/grep -Fq \
            'required_groups=(i2c openrazer realtime wheel)' \
            ${arch-switch}/bin/arch-switch
          if ${arch-switch}/bin/arch-switch --check --update > /dev/null 2>&1; then
            printf 'arch-switch accepted incompatible modes\n' >&2
            exit 1
          fi
          ${archDeployment}/bin/${deploymentName} --help \
            | ${pkgs.gnugrep}/bin/grep -Fxq \
              'usage: ${deploymentName} [--update] [HOME_MANAGER_ARGUMENTS...]'
          touch "$out"
        '';
        arch-graphical-session = pkgs.runCommand "arch-graphical-session-check" { } ''
          units=${archHomes.${homeConfigurationName}.activationPackage}/home-files/.config/systemd/user
          profile=${archHomes.${homeConfigurationName}.config.home.path}
          for unit in \
            hyprpolkitagent.service \
            keepassxc.service \
            noctalia.service \
            polychromatic-tray.service \
            quickshell-overview.service \
            remmina-applet.service \
            tailscale-systray.service \
            vesktop.service \
            vicinae.service; do
            if ${pkgs.gnugrep}/bin/grep -Eq '^Exec(Start|StartPre|StartPost|Reload)=.*/nix/store/' "$units/$unit"; then
              printf 'Arch graphical unit references a Nix package: %s\n' "$unit" >&2
              exit 1
            fi
          done
          for unit in \
            polychromatic-tray.service \
            remmina-applet.service \
            tailscale-systray.service \
            vesktop.service \
            vicinae.service; do
            if ! ${pkgs.gnugrep}/bin/grep -qx 'After=noctalia.service' "$units/$unit"; then
              printf 'Tray consumer does not start after Noctalia: %s\n' "$unit" >&2
              exit 1
            fi
          done
          if ! ${pkgs.gnugrep}/bin/grep -q '^ExecStartPre=.*StatusNotifierWatcher' "$units/vicinae.service"; then
            printf 'Vicinae does not wait for Noctalia tray readiness\n' >&2
            exit 1
          fi
          if ! ${pkgs.gnugrep}/bin/grep -qx \
            'Environment=VICINAE_OVERRIDES=%h/.config/vicinae/nix-managed.json' \
            "$units/vicinae.service"; then
            printf 'Vicinae does not load the managed launcher policy\n' >&2
            exit 1
          fi
          for application in kitty vesktop; do
            if ! ${pkgs.gnugrep}/bin/grep -q \
              "\"$application\":{\"preferences\":{\"defaultAction\":\"launch\"}}" \
              "$units/../../vicinae/nix-managed.json"; then
              printf 'Vicinae does not launch a new %s instance by default\n' "$application" >&2
              exit 1
            fi
          done
          for executable in \
            ghostty \
            gimp \
            hypridle \
            hyprlock \
            hyprpolkitagent \
            hyprsunset \
            keepassxc \
            kitty \
            mpv \
            mpvpaper \
            noctalia \
            noctalia-shell \
            obs \
            quickshell \
            remmina \
            swappy \
            uwsm \
            vesktop \
            vicinae \
            vlc; do
            if [[ -e "$profile/bin/$executable" ]]; then
              printf 'Arch Home profile provides a native graphical executable: %s\n' "$executable" >&2
              exit 1
            fi
          done
          touch "$out"
        '';
        gitlab-runner-config = pkgs.runCommand "gitlab-runner-config-check" { } ''
          ${runnerctl}/bin/runnerctl validate > "$out"
        '';
        gitlab-runner-interface =
          assert runnerInterfaceTests;
          pkgs.writeText "gitlab-runner-interface-check" "GitLab Runner Interface checks passed\n";
        gitlab-runner-tests =
          pkgs.runCommand "gitlab-runner-tests"
            {
              nativeBuildInputs = [ pkgs.python3 ];
            }
            ''
              python ${./modules/gitlab-runner/runnerctl_test.py} \
                ${
                  pkgs.writeText "gitlab-runner-test-instances.json" (
                    builtins.toJSON {
                      instances = runnerInstances;
                      platform = runnerPlatform;
                    }
                  )
                } \
                ${./modules/gitlab-runner/runnerctl.py}
              touch "$out"
            '';
        justfile =
          pkgs.runCommand "justfile-check"
            {
              nativeBuildInputs = [ pkgs.just ];
            }
            ''
              just --justfile ${./Justfile} --summary > "$out"
              grep -Fxq 'arch-workstation build check check-arch default' "$out"
              just --justfile ${./Justfile} --dry-run arch-workstation update >> "$out" 2>&1
              grep -Fq 'nix run .#arch-workstation -- --update' "$out"
            '';
      };

      packages.${system} = {
        inherit arch-switch home-switch runnerctl;
        ${deploymentName} = archDeployment;
        default = arch-switch;
      };

      apps.${system} = {
        arch-switch = {
          type = "app";
          program = "${arch-switch}/bin/arch-switch";
          meta.description = "Converge Arch-native workstation policy";
        };
        ${deploymentName} = {
          type = "app";
          program = "${archDeployment}/bin/${deploymentName}";
          meta.description = "Build and activate ${deploymentName}";
        };
        home-switch = {
          type = "app";
          program = "${home-switch}/bin/home-switch";
          meta.description = "Activate ${homeConfigurationName} through Home Manager";
        };
        just = {
          type = "app";
          program = "${pkgs.just}/bin/just";
          meta.description = "Run project commands before Home Manager is active";
        };
        runnerctl = {
          type = "app";
          program = "${runnerctl}/bin/runnerctl";
          meta.description = "Manage dedicated rootless GitLab Runner instances";
        };
      };

      formatter.${system} = pkgs.nixfmt;
    };
}
