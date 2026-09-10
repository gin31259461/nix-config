set shell := ["bash", "-euo", "pipefail", "-c"]

# List the available project commands.
default:
    @just --list

# Evaluate and build every flake check with complete build logs.
check:
    nix flake check --show-trace --print-build-logs

# Check formatting and stable interfaces without building the full home.
check-fast:
    nix build --no-link --show-trace --print-build-logs \
      .#checks.x86_64-linux.source-format \
      .#checks.x86_64-linux.host-interface \
      .#checks.x86_64-linux.gitlab-runner-interface \
      .#checks.x86_64-linux.system-settings-interface

# Query remote Arch, LizardByte, and AUR inventories.
check-arch:
    nix run --show-trace --print-build-logs .#arch-switch -- --check

# Build a deployment without activation.
build deployment="arch-workstation":
    nix build --no-link --show-trace --print-build-logs ".#{{ deployment }}"

# Prepare the selected pinned llama.cpp build and model.
prepare-ai mode="":
    #!/usr/bin/env bash
    set -euo pipefail
    case {{ quote(mode) }} in
      '') exec sudo nix --extra-experimental-features 'nix-command flakes' run --show-trace --print-build-logs .#llama-prepare ;;
      build) exec sudo nix --extra-experimental-features 'nix-command flakes' run --show-trace --print-build-logs .#llama-prepare -- --build-only ;;
      model) exec sudo nix --extra-experimental-features 'nix-command flakes' run --show-trace --print-build-logs .#llama-prepare -- --model-only ;;
      *) printf '%s\n' 'usage: just prepare-ai [build|model]' >&2; exit 2 ;;
    esac

# Reconcile one configured GitLab Runner instance before registration.
prepare-runner instance:
    sudo nix --extra-experimental-features 'nix-command flakes' run --show-trace --print-build-logs .#runnerctl -- reconcile {{ quote(instance) }}

# Register and verify one prepared GitLab Runner. Requires GITLAB_RUNNER_TOKEN.
initialize-runner instance:
    #!/usr/bin/env bash
    set -euo pipefail
    [[ -n ${GITLAB_RUNNER_TOKEN:-} ]] || {
      printf '%s\n' 'GITLAB_RUNNER_TOKEN is required' >&2
      exit 2
    }
    exec sudo --preserve-env=GITLAB_RUNNER_TOKEN \
      nix --extra-experimental-features 'nix-command flakes' run --show-trace --print-build-logs .#runnerctl -- register {{ quote(instance) }}

# Verify a configured GitLab Runner instance.
verify-runner instance:
    sudo nix --extra-experimental-features 'nix-command flakes' run --show-trace --print-build-logs .#runnerctl -- verify {{ quote(instance) }}

# Show the current state of a configured GitLab Runner instance.
status-runner instance:
    sudo nix --extra-experimental-features 'nix-command flakes' run --show-trace --print-build-logs .#runnerctl -- status {{ quote(instance) }}

# Build and activate the Arch workstation; combine update and verbose as needed.
arch-workstation option1="" option2="":
    #!/usr/bin/env bash
    set -euo pipefail
    readonly usage='usage: just arch-workstation [update] [verbose]'
    options=({{ quote(option1) }} {{ quote(option2) }})
    deployment_args=()
    nix_args=(--show-trace --print-build-logs)
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
    if (( verbose_seen )); then
      deployment_args+=(--verbose)
      nix_args+=(--verbose)
    fi
    nix build --no-link "${nix_args[@]}" .#arch-workstation
    if ((${#deployment_args[@]})); then
      exec nix run "${nix_args[@]}" .#arch-workstation -- "${deployment_args[@]}"
    else
      exec nix run "${nix_args[@]}" .#arch-workstation
    fi
