set shell := ["bash", "-euo", "pipefail", "-c"]

# List the available project commands.
default:
    @just --list

# Evaluate and build every flake check.
check:
    nix flake check

# Check Nix/Python formatting and Python static errors without building the home.
check-fast:
    nix build --no-link .#checks.x86_64-linux.source-format .#checks.x86_64-linux.host-interface .#checks.x86_64-linux.gitlab-runner-interface .#checks.x86_64-linux.system-settings-interface

# Query the remote Arch, LizardByte, and AUR inventories (requires connectivity).
check-arch:
    nix run .#arch-switch -- --check

# Build a deployment without activating it.
build deployment="arch-workstation":
    nix build --no-link ".#{{ deployment }}"

# Build and activate the Arch workstation; combine `update` and `verbose` as needed.
arch-workstation option1="" option2="":
    #!/usr/bin/env bash
    set -euo pipefail
    readonly usage='usage: just arch-workstation [update] [verbose]'
    options=({{ quote(option1) }} {{ quote(option2) }})
    deployment_args=()
    update_seen=0
    verbose_seen=0
    for option in "${options[@]}"; do
      case "$option" in
        '') ;;
        update)
          (( update_seen == 0 )) || { printf '%s\n' "$usage" >&2; exit 2; }
          update_seen=1
          ;;
        verbose)
          (( verbose_seen == 0 )) || { printf '%s\n' "$usage" >&2; exit 2; }
          verbose_seen=1
          ;;
        *) printf '%s\n' "$usage" >&2; exit 2 ;;
      esac
    done
    (( update_seen == 0 )) || deployment_args+=(--update)
    (( verbose_seen == 0 )) || deployment_args+=(--verbose)
    nix build --no-link .#arch-workstation
    if ((${#deployment_args[@]})); then
      nix run .#arch-workstation -- "${deployment_args[@]}"
    else
      nix run .#arch-workstation
    fi
