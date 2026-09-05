{
  description = "Arch workstation deployment and Home Manager configuration";
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
      archHost = import ./lib/validate-host.nix {
        inherit lib;
        raw = import ./hosts/arch;
      };
      archHomes = lib.mapAttrs' (
        username: user:
        lib.nameValuePair "${username}@${archHost.name}" (mkHomeConfiguration {
          inherit username user;
          hostName = archHost.name;
          platform = archHost.platform;
          hardware = archHost.hardware;
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
      runners = import ./modules/gitlab-runner {
        inherit lib pkgs;
        rawInstances = archHost.gitlabRunners;
      };
      nativePackages = import ./platforms/arch/packages.nix {
        inherit lib;
        hardware = archHost.hardware;
        modulePackages = runners.requiredPackages;
      };
      arch-switch = import ./platforms/arch/package.nix {
        inherit lib pkgs deploymentUser;
        username = deployment.username;
        packages = nativePackages;
        hardware = archHost.hardware;
      };
      home-switch = pkgs.writeShellApplication {
        name = "home-switch";
        runtimeInputs = [ inputs.home-manager.packages.${system}.home-manager ];
        text = ''
          for argument in "$@"; do
            case "$argument" in
              -b*|--backup-file-extension*)
                printf 'Adjacent Home Manager backups are not supported; resolve the conflicting path first.\n' >&2
                exit 2 ;;
            esac
          done
          exec home-manager switch --flake '${self}#${homeConfigurationName}' "$@"
        '';
      };
      archDeployment = pkgs.writeShellApplication {
        name = deploymentName;
        text = ''
          readonly deployment_name=${lib.escapeShellArg deploymentName}
          readonly activation_package=${archHomes.${homeConfigurationName}.activationPackage}
          readonly arch_switch=${arch-switch}/bin/arch-switch
          readonly home_switch=${home-switch}/bin/home-switch
        ''
        + builtins.readFile ./lib/deploy-home.sh;
      };
    in
    assert lib.assertMsg (builtins.elem deployment.profile deploymentUser.profiles)
      "deployment profile ${deployment.profile} is not selected by ${deployment.username}";
    assert lib.assertMsg deploymentUser.admin
      "deployment user ${deployment.username} must be an administrator";
    {
      homeConfigurations = archHomes;

      checks.${system} = {
        optional-modules = import ./checks/optional-modules.nix { inherit lib pkgs inputs; };
        source-format = import ./checks/format.nix { inherit lib pkgs; };
        arch-home = archHomes.${homeConfigurationName}.activationPackage;
        host-interface =
          assert import ./checks/host-interface.nix { inherit lib pkgs; };
          pkgs.writeText "host-interface" "passed";
      }
      // (import ./checks {
        inherit
          pkgs
          arch-switch
          archDeployment
          deploymentName
          ;
      })
      // (import ./modules/home/checks.nix {
        inherit pkgs;
        home = archHomes.${homeConfigurationName};
      })
      // runners.checks;

      packages.${system} = {
        inherit arch-switch home-switch;
        ${deploymentName} = archDeployment;
        default = arch-switch;
      }
      // runners.packages;

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
      }
      // runners.apps;

      formatter.${system} = pkgs.nixfmt;
    };
}
