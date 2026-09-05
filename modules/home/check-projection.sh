# Read-only preflight before Home Manager changes either external input path.
for target in "$home_dir/.config/nvim" "$home_dir/.config/hypr"; do
  for directory in "$target" "$(realpath -m "$target")"; do
    while :; do
      if [[ -e $directory/.git || -L $directory/.git ]]; then
        printf 'Refusing configuration projection into a Git worktree: %s\n' "$target" >&2
        exit 1
      fi
      [[ $directory == / ]] && break
      directory=$(dirname "$directory")
    done
  done
  for suffix in .bak .backup '~'; do
    if [[ -e $target$suffix || -L $target$suffix ]]; then
      printf 'Resolve the adjacent configuration backup before activation: %s\n' "$target$suffix" >&2
      exit 1
    fi
  done
done
