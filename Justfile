set shell := ["bash", "-euo", "pipefail", "-c"]

# List the available project commands.
default:
    @just --list

# Evaluate and build every flake check.
check:
    nix flake check

# Check Nix/Python formatting and Python static errors without building the home.
check-fast:
    nix build --no-link .#checks.x86_64-linux.source-format .#checks.x86_64-linux.host-interface .#checks.x86_64-linux.gitlab-runner-interface

# Query the remote Arch, LizardByte, and AUR inventories (requires connectivity).
check-arch:
    nix run .#arch-switch -- --check

# Build a deployment without activating it.
build deployment="arch-workstation":
    nix build --no-link ".#{{ deployment }}"

# Build and activate the Arch workstation; pass `update` for a full system update.
arch-workstation mode="switch": (build "arch-workstation")
    #!/usr/bin/env bash
    set -euo pipefail
    case '{{ mode }}' in
      switch) nix run .#arch-workstation ;;
      update) nix run .#arch-workstation -- --update ;;
      *) printf 'usage: just arch-workstation [update]\n' >&2; exit 2 ;;
    esac
