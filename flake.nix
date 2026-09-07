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
          ai = archHost.ai;
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
      ai = import ./modules/ai {
        inherit lib;
        config = archHost.ai;
      };
      virtualization = import ./modules/virtualization {
        inherit lib;
        config = archHost.virtualization;
      };
      systemSettings = import ./platforms/arch/system {
        inherit lib pkgs;
        config = archHost.systemSettings;
        hostName = archHost.name;
      };
      nativePackages = import ./platforms/arch/packages.nix {
        inherit lib;
        hardware = archHost.hardware;
        modulePackages = runners.requiredPackages ++ virtualization.requiredPackages;
        systemSettings = archHost.systemSettings;
        moduleAurPackages = ai.aurPackages;
      };
      arch-switch = import ./platforms/arch/package.nix {
        inherit
          lib
          pkgs
          deploymentUser
          systemSettings
          ;
        moduleGroups = virtualization.loginGroups;
        moduleSystemUnits = virtualization.systemUnits;
        username = deployment.username;
        packages = nativePackages;
        hardware = archHost.hardware;
      };
      home-switch = import ./lib/deployment/home/package.nix {
        inherit pkgs;
        activationPackage = archHomes.${homeConfigurationName}.activationPackage;
      };
      noctalia-config = import ./modules/home/noctalia-config/package.nix {
        inherit pkgs;
        username = deployment.username;
        homeConfiguration = homeConfigurationName;
      };
      archDeployment = import ./lib/deployment/package.nix {
        inherit
          lib
          pkgs
          deploymentName
          arch-switch
          home-switch
          ;
      };
    in
    {
      homeConfigurations = archHomes;

      checks.${system} = {
        capabilities = import ./checks/capabilities.nix { inherit lib pkgs inputs; };
        optional-modules = import ./checks/optional-modules.nix { inherit lib pkgs inputs; };
        source-format = import ./checks/format.nix { inherit lib pkgs; };
        arch-home = archHomes.${homeConfigurationName}.activationPackage;
      }
      // (import ./checks {
        inherit
          lib
          pkgs
          arch-switch
          archDeployment
          deploymentName
          ;
      })
      // (import ./platforms/arch/checks.nix { inherit pkgs arch-switch; })
      // (import ./modules/home/checks.nix {
        inherit pkgs inputs;
        home = archHomes.${homeConfigurationName};
      })
      // runners.checks;

      packages.${system} = {
        inherit arch-switch home-switch noctalia-config;
        ${deploymentName} = archDeployment;
        default = arch-switch;
      }
      // runners.packages;

      apps.${system} = {
        noctalia-config = {
          type = "app";
          program = "${noctalia-config}/bin/noctalia-config";
          meta.description = "Capture or deploy reviewed Noctalia preferences";
        };
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
