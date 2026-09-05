arch_switch_args=()
if [[ ${1-} == --update ]]; then
  arch_switch_args+=(--update)
  shift
elif [[ ${1-} == --help ]]; then
  printf 'usage: %s [--update] [HOME_MANAGER_ARGUMENTS...]\n' "$deployment_name"
  exit 0
fi
for argument in "$@"; do
  case "$argument" in
    -b*|--backup-file-extension*)
      printf 'Adjacent Home Manager backups are not supported; resolve the conflicting path first.\n' >&2
      exit 2 ;;
  esac
done
if [[ ! -x $activation_package/activate ]]; then
  printf 'Home Manager activation package is unavailable\n' >&2
  exit 1
fi
"$arch_switch" "${arch_switch_args[@]}"
exec "$home_switch" "$@"
