# Private implementation. package.nix supplies all paths and declared values.
# The test harness supplies an isolated filesystem and fake native commands.
usage() { printf 'usage: arch-switch [--check | --update]\n'; }
native() { "$native_bin/$1" "${@:2}"; }
root() { native sudo "$native_bin/$1" "${@:2}"; }
fail() { printf '%s\n' "$1" >&2; exit "${2:-1}"; }

check_only=0
update_system=0
for argument in "$@"; do
  case "$argument" in
    --check) check_only=1 ;;
    --update) update_system=1 ;;
    --help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
if (( check_only && update_system )); then usage >&2; exit 2; fi

[[ -e $fs_root/etc/arch-release ]] || fail 'arch-switch only supports Arch Linux'
[[ $(native id -u) != 0 ]] || fail 'run arch-switch as the login user, not root'
login_user=$(native id --user --name)
[[ $login_user == "$expected_user" ]] || fail "arch-switch must run as $expected_user, not $login_user"
has_group() { native id -nG "$login_user" | tr ' ' '\n' | grep -Fxq "$1"; }
has_group wheel || fail 'deployment user is not in required administrator group: wheel'

# Check every native dependency before any mutation. Nix supplies text utilities.
for command in id sudo pacman pacman-conf yay install mv rm touch mkdir mktemp \
  systemctl sysctl gpasswd getcap setcap mkinitcpio modprobe; do
  [[ -x $native_bin/$command ]] || fail "required command is missing: $native_bin/$command"
done

work_dir=$(mktemp -d)
pending_file=''
cleanup() {
  if [[ -n $pending_file ]]; then root rm -f -- "$pending_file"; fi
  rm -rf -- "$work_dir"
}
trap cleanup EXIT

resolve_inventory() {
  native pacman --sync --print --needed -- "${pacman_packages[@]}" >/dev/null
  "$curl_bin" --fail --location --show-error --silent --connect-timeout 10 --max-time 60 \
    --output "$work_dir/lizardbyte.db" "$lizardbyte_server/lizardbyte.db"
  "$tar_bin" -tf "$work_dir/lizardbyte.db" > "$work_dir/lizardbyte-files"
  for package in "${lizardbyte_package_names[@]}"; do
    grep -Eq "^$package-[^/]+/desc$" "$work_dir/lizardbyte-files" \
      || fail "LizardByte package did not resolve: $package"
  done
  if (( ${#aur_packages[@]} )); then
    native yay --sync --info -- "${aur_packages[@]}" >/dev/null
  fi
}
lizardbyte_server=$(native pacman-conf --config "$files/pacman-lizardbyte.conf" --repo lizardbyte Server)
if (( check_only )); then
  resolve_inventory
  printf 'Arch, LizardByte, and AUR package inventories resolve\n'
  exit 0
fi

# Only the selected login user can deploy. Its private runtime directory also
# serializes update and routine activation; the lock inode is never removed.
runtime_dir="$fs_root/run/user/$(native id -u)"
[[ -d $runtime_dir && ! -L $runtime_dir ]] || fail 'login runtime directory is unavailable'
exec {lock_fd}>"$runtime_dir/nix-config-arch.lock"
"$flock_bin" -n "$lock_fd" || fail 'another arch-switch is running' 75

missing_packages=()
for package in "${pacman_packages[@]}" "${lizardbyte_package_names[@]}" "${aur_packages[@]}"; do
  native pacman --query -- "$package" >/dev/null 2>&1 || missing_packages+=("$package")
done
if (( ! update_system && ${#missing_packages[@]} )); then
  printf 'declared Arch packages are missing; rerun with --update to install them safely:\n' >&2
  printf '  %s\n' "${missing_packages[@]}" >&2
  exit 3
fi
running_kernel=$(uname -r)
check_kernel() {
  [[ -d $fs_root/usr/lib/modules/$running_kernel ]] \
    || fail "kernel modules do not match running kernel $running_kernel; reboot, then rerun the deployment" 75
}
check_kernel
repo_file="$fs_root/etc/pacman.d/nix-config-lizardbyte.conf"
repo_include='Include = /etc/pacman.d/nix-config-lizardbyte.conf'
if ! grep -Fxq "$repo_include" "$fs_root/etc/pacman.conf" \
  && native pacman-conf --repo lizardbyte Server >/dev/null 2>&1; then
  fail 'an unmanaged [lizardbyte] repository already exists in pacman.conf'
fi
if (( update_system )); then resolve_inventory; fi

root_state="$fs_root/var/lib/nix-config/arch"
native sudo -v
root install -d -m0755 -o0 -g0 "$root_state"
changed_files=0
actions=0

# Mark pending actions BEFORE replacing a file. A failed action (or interrupted
# write) remains pending across invocations even when the file already matches.
ensure_file() {
  local source=$1 target=$2 action=${3:-}
  [[ ! -L $target ]] || fail "managed file is a symlink: $target"
  if [[ -f $target ]] && cmp -s "$source" "$target" \
    && [[ $(stat -c '%a:%u:%g' "$target") == "$managed_identity" ]]; then
    return 0
  fi
  if [[ -n $action ]]; then root touch "$root_state/$action.pending"; fi
  root mkdir -p -- "$(dirname "$target")"
  pending_file=$(root mktemp "$(dirname "$target")/.nix-config.XXXXXXXX")
  root install -m0644 -o0 -g0 -- "$source" "$pending_file"
  root mv -fT -- "$pending_file" "$target"
  pending_file=''
  changed_files=$((changed_files + 1))
  printf 'updated %s\n' "${target#"$fs_root"}"
}
ensure_file "$files/pacman-lizardbyte.conf" "$repo_file"
if ! grep -Fxq "$repo_include" "$fs_root/etc/pacman.conf"; then
  { cat "$fs_root/etc/pacman.conf"; printf '\n%s\n' "$repo_include"; } > "$work_dir/pacman.conf"
  ensure_file "$work_dir/pacman.conf" "$fs_root/etc/pacman.conf"
fi
[[ $(native pacman-conf --repo lizardbyte Server) == "$lizardbyte_server" ]] \
  || fail 'managed [lizardbyte] repository did not load as expected'
if (( update_system )); then
  root pacman --sync --refresh --sysupgrade --needed --noconfirm -- \
    "${pacman_packages[@]}" "${lizardbyte_packages[@]}"
  check_kernel
  if (( ${#aur_packages[@]} )); then native yay --sync --needed --noconfirm -- "${aur_packages[@]}"; fi
fi

ensure_file "$files/NetworkManager-main.conf" "$fs_root/etc/NetworkManager/conf.d/main.conf" network
ensure_file "$files/NetworkManager-tailscale.conf" "$fs_root/etc/NetworkManager/conf.d/99-tailscale.conf" network
ensure_file "$files/container-network-modules.conf" "$fs_root/etc/modules-load.d/nix-config-podman.conf"
ensure_file "$files/sysctl.conf" "$fs_root/etc/sysctl.d/99-nix-config.conf"
sed "s/@USER@/$login_user/g" "$files/tty1-autologin.conf" > "$work_dir/autologin.conf"
ensure_file "$work_dir/autologin.conf" "$fs_root/etc/systemd/system/getty@tty1.service.d/override.conf" units

# Own only this marked addition, preserving administrator MODULES and HOOKS.
awk '
  /^# BEGIN nix-config modules$/ { if (managed) exit 1; managed = 1; next }
  /^# END nix-config modules$/ { if (!managed) exit 1; managed = 0; next }
  !managed { print }
  END { if (managed) exit 1 }
' "$fs_root/etc/mkinitcpio.conf" > "$work_dir/mkinitcpio.conf"
{
  printf '# BEGIN nix-config modules\nMODULES+=('
  printf ' %s' "${initramfs_modules[@]}"
  printf ' )\n# END nix-config modules\n'
} >> "$work_dir/mkinitcpio.conf"
ensure_file "$work_dir/mkinitcpio.conf" "$fs_root/etc/mkinitcpio.conf" initramfs
for image in "${initramfs_images[@]}"; do
  if [[ ! -s $fs_root$image ]]; then root touch "$root_state/initramfs.pending"; fi
done
if [[ -e $root_state/initramfs.pending ]]; then
  root mkinitcpio -P
  for image in "${initramfs_images[@]}"; do
    [[ -s $fs_root$image ]] || fail "initramfs was not generated: $image"
  done
  root rm -- "$root_state/initramfs.pending"
  actions=$((actions + 1))
fi
groups_changed=0
for group in "${required_groups[@]}"; do
  if ! has_group "$group"; then root gpasswd --add "$login_user" "$group"; groups_changed=1; fi
done

if [[ -e $root_state/units.pending ]]; then
  root systemctl daemon-reload
  root rm -- "$root_state/units.pending"
  actions=$((actions + 1))
fi
for service in NetworkManager.service bluetooth.service power-profiles-daemon.service tailscaled.service; do
  if ! native systemctl is-enabled --quiet "$service"; then root systemctl enable "$service"; actions=$((actions + 1)); fi
  if ! native systemctl is-active --quiet "$service"; then root systemctl start "$service"; actions=$((actions + 1)); fi
done
if [[ -e $root_state/network.pending ]]; then
  root systemctl restart NetworkManager.service
  root rm -- "$root_state/network.pending"
  actions=$((actions + 1))
fi
# Compare runtime values too: unchanged files must not conceal runtime drift.
while IFS= read -r module; do
  [[ -n $module && $module != \#* ]] || continue
  if [[ ! -d $fs_root/sys/module/$module ]]; then
    root modprobe "$module"
    actions=$((actions + 1))
  fi
done < "$files/container-network-modules.conf"
while IFS='=' read -r key desired; do
  key=$(printf '%s' "$key" | xargs)
  [[ -n $key && $key != \#* ]] || continue
  desired=$(printf '%s' "$desired" | xargs)
  actual=$(native sysctl -n "$key")
  if [[ $actual != "$desired" ]]; then root sysctl -w "$key=$desired"; actions=$((actions + 1)); fi
done < "$files/sysctl.conf"
for service in "${user_services[@]}"; do
  if ! native systemctl --user is-enabled --quiet "$service"; then
    native systemctl --user enable "$service"
    actions=$((actions + 1))
  fi
done
sunshine=$(readlink -f "$native_bin/sunshine")
[[ -f $sunshine ]] || fail 'Sunshine executable is missing'
if [[ $(native getcap "$sunshine") != "$sunshine cap_sys_admin=p" ]]; then
  root setcap cap_sys_admin+p "$sunshine"
  actions=$((actions + 1))
fi
printf 'Arch converged: %s files updated, %s runtime actions.\n' "$changed_files" "$actions"
if (( groups_changed )); then printf 'Group membership changed; log out and back in.\n'; fi
