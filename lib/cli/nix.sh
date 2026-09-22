# Sourced by Just recipes before Nix builds the runtime progress module.
# Keep diagnostic flags and privilege/token handling with the caller.
nix_progress_init() {
  nix_progress_args=(--log-format raw)
  if [[ -t 2 && ${TERM:-dumb} != dumb && ! -v NO_COLOR && -z ${CI:-} ]] &&
    [[ ${1:-0} == 0 ]]; then
    nix_progress_args=(--log-format bar-with-logs)
  fi
}
