arch_switch_args=()
if [[ ${1-} == --update ]]; then
  arch_switch_args+=(--update)
  shift
elif [[ ${1-} == --help ]]; then
  printf 'usage: %s [--update] [--verbose]\n' "$deployment_name"
  exit 0
fi
for argument in "$@"; do
  case "$argument" in
    --verbose) ;;
    *) printf 'usage: %s [--update] [--verbose]\n' "$deployment_name" >&2; exit 2 ;;
  esac
done
"$arch_switch" "${arch_switch_args[@]}"
exec "$home_switch" "$@"
