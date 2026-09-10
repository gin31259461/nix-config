arch_switch_args=()
home_switch_args=()
update_seen=0
verbose_seen=0
for argument in "$@"; do
  case "$argument" in
    --update)
      (( update_seen == 0 )) || { printf 'usage: %s [--update] [--verbose]\n' "$deployment_name" >&2; exit 2; }
      update_seen=1
      arch_switch_args+=(--update)
      ;;
    --verbose)
      (( verbose_seen == 0 )) || { printf 'usage: %s [--update] [--verbose]\n' "$deployment_name" >&2; exit 2; }
      verbose_seen=1
      arch_switch_args+=(--verbose)
      home_switch_args+=(--verbose)
      ;;
    --help)
      if (($# == 1)); then
        printf 'usage: %s [--update] [--verbose]\n' "$deployment_name"
        exit 0
      fi
      printf 'usage: %s [--update] [--verbose]\n' "$deployment_name" >&2
      exit 2
      ;;
    *)
      printf 'usage: %s [--update] [--verbose]\n' "$deployment_name" >&2
      exit 2
      ;;
  esac
done
"$arch_switch" "${arch_switch_args[@]}"
exec "$home_switch" "${home_switch_args[@]}"
