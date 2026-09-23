arch_switch_args=()
home_switch_args=()
update_seen=0
purge_seen=0
verbose_seen=0
for argument in "$@"; do
  case "$argument" in
    --update)
      (( update_seen == 0 )) || { printf 'usage: %s [--update] [--purge] [--verbose]\n' "$deployment_name" >&2; exit 2; }
      update_seen=1
      arch_switch_args+=(--update)
      ;;
    --purge)
      (( update_seen == 0 )) || { printf 'usage: %s [--update] [--purge] [--verbose]\n' "$deployment_name" >&2; exit 2; }
      update_seen=1
      purge_seen=1
      arch_switch_args+=(--purge)
      ;;
    --verbose)
      (( verbose_seen == 0 )) || { printf 'usage: %s [--update] [--purge] [--verbose]\n' "$deployment_name" >&2; exit 2; }
      verbose_seen=1
      arch_switch_args+=(--verbose)
      home_switch_args+=(--verbose)
      ;;
    --help)
      if (($# == 1)); then
        printf 'usage: %s [--update] [--purge] [--verbose]\n' "$deployment_name"
        exit 0
      fi
      printf 'usage: %s [--update] [--purge] [--verbose]\n' "$deployment_name" >&2
      exit 2
      ;;
    *)
      printf 'usage: %s [--update] [--purge] [--verbose]\n' "$deployment_name" >&2
      exit 2
      ;;
  esac
done
printf '\n==> Phase 1/2: Arch System Convergence <==\n\n' >&2
"$arch_switch" "${arch_switch_args[@]}"
if ((purge_seen)); then
  exit 0
fi
printf '\n==> Phase 2/2: Home Manager Activation <==\n\n' >&2
exec "$home_switch" "${home_switch_args[@]}"
