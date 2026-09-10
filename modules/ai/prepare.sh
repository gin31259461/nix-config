usage() { printf 'usage: llama-prepare [--build-only | --model-only]\n'; }
build=1
model=1
case "${1:-}" in
  '') ;;
  --build-only) model=0 ;;
  --model-only) build=0 ;;
  --help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

((EUID == 0)) || { printf 'run llama-prepare as root (sudo nix run .#llama-prepare)\n' >&2; exit 1; }
work=$(mktemp -d /var/tmp/nix-config-llama.XXXXXXXX)
chmod 0700 "$work"
trap 'rm -rf -- "$work"' EXIT
exec {lock_fd}>/run/lock/nix-config-llama-prepare.lock
flock -n "$lock_fd" || { printf 'another llama-prepare is running\n' >&2; exit 75; }
if ((build)); then
  [[ -x /usr/bin/c++ && -x /opt/rocm/bin/hipcc && -f /usr/include/vulkan/vulkan.h ]] || {
    printf 'native C++, ROCm, or Vulkan development toolchain is missing\n' >&2; exit 1;
  }
  revision_dir="$install_prefix/revisions/$source_revision-$grammar_threshold"
  receipt="$revision_dir/nix-config-build"
  receipt_text="$source_revision $grammar_threshold"
  [[ ! -L $revision_dir ]] || { printf 'revision path must not be a symlink\n' >&2; exit 1; }
  if [[ -e $revision_dir ]]; then
    [[ -f $receipt && $(<"$receipt") == "$receipt_text" && -x $revision_dir/bin/llama-server ]] || {
      printf 'existing llama.cpp revision directory is not owned by this declaration\n' >&2
      exit 1
    }
  else
    git clone --filter=blob:none --no-checkout -- "$source_repository" "$work/llama.cpp"
    git -C "$work/llama.cpp" checkout --detach "$source_revision"
    grammar="$work/llama.cpp/src/llama-grammar.cpp"
    expected='#define MAX_REPETITION_THRESHOLD 2000'
    [[ $(grep -Fxc "$expected" "$grammar") == 1 ]] || {
      printf 'pinned source no longer contains the reviewed grammar threshold\n' >&2
      exit 1
    }
    sed -i "s/$expected/#define MAX_REPETITION_THRESHOLD $grammar_threshold/" "$grammar"
    cmake -S "$work/llama.cpp" -B "$work/build" -G Ninja \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$work/install" \
      -DVulkan_INCLUDE_DIR=/usr/include -DVulkan_LIBRARY=/usr/lib/libvulkan.so \
      -DGGML_HIP=ON -DGGML_VULKAN=ON -DLLAMA_CURL=ON
    cmake --build "$work/build" --target install
    stage="$install_prefix/revisions/.nix-config-$source_revision-$grammar_threshold"
    install -d -m0755 -o0 -g0 "$install_prefix/revisions"
    [[ ! -e $stage && ! -L $stage ]] || { printf 'stale llama.cpp preparation stage requires operator review\n' >&2; exit 1; }
    cp -a "$work/install" "$stage"
    chown -R 0:0 "$stage"
    printf '%s\n' "$receipt_text" >"$stage/nix-config-build"
    chmod 0644 "$stage/nix-config-build"
    mv -T "$stage" "$revision_dir"
  fi
  link_stage="$install_prefix/.current-$source_revision-$grammar_threshold"
  desired_link="revisions/$source_revision-$grammar_threshold"
  if [[ -L $install_prefix/current ]]; then
    current_link=$(readlink "$install_prefix/current")
    [[ -d $install_prefix/current ]] || { printf 'current llama.cpp selector is dangling\n' >&2; exit 1; }
    [[ $current_link == "$desired_link" ]] ||
      [[ $current_link =~ ^revisions/[0-9a-f]{40}-[0-9]+$ ]] || {
        printf 'existing current link is not owned by llama-prepare\n' >&2; exit 1;
      }
  elif [[ -e $install_prefix/current ]]; then
    printf 'existing current path is not owned by llama-prepare\n' >&2; exit 1
  fi
  if [[ ${current_link:-} != "$desired_link" ]]; then
    ln -s "$desired_link" "$link_stage"
    mv -Tf "$link_stage" "$install_prefix/current"
  fi
fi
if ((model)); then
  [[ ! -L $model_path ]] || { printf 'model path must not be a symlink\n' >&2; exit 1; }
  current=''
  if [[ -f $model_path ]]; then current=$(sha256sum "$model_path" | cut -d' ' -f1); fi
  if [[ -n $current && $current != "$model_sha256" ]]; then
    printf 'existing model checksum differs; preserve or relocate it before preparation\n' >&2
    exit 1
  fi
  if [[ -z $current ]]; then
    model_dir=$(dirname "$model_path")
    model_stage="$model_dir/.nix-config-$model_file"
    [[ ! -L $model_dir ]] || { printf 'model directory must not be a symlink\n' >&2; exit 1; }
    install -d -m0755 -o0 -g0 "$model_dir"
    [[ ! -e $model_stage && ! -L $model_stage ]] || { printf 'stale model preparation stage requires operator review\n' >&2; exit 1; }
    install -m0600 -o0 -g0 /dev/null "$model_stage"
    curl --fail --location --show-error --output "$model_stage" \
      "https://huggingface.co/$model_repository/resolve/$model_revision/$model_file"
    printf '%s  %s\n' "$model_sha256" "$model_stage" | sha256sum --check --status
    chmod 0644 "$model_stage"
    mv -T "$model_stage" "$model_path"
  fi
fi
printf 'llama.cpp preparation complete\n'
