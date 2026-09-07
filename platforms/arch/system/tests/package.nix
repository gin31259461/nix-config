# Private upstream UFW fixture for the isolated VM, never a home/native package.
{ pkgs }:
let
  src = pkgs.fetchurl {
    url = "https://launchpad.net/ufw/0.36/0.36.2/+download/ufw-0.36.2.tar.gz";
    sha256 = "1xcbhd1xck205vi5cm26z1ckgbhbnch2bv9p6pdl8szgxjgajmra";
  };
in
pkgs.runCommand "ufw-test-fixture-0.36.2"
  {
    nativeBuildInputs = [ pkgs.makeWrapper ];
  }
  ''
    tar xf ${src}
    cd ufw-0.36.2
    mkdir -p "$out/lib/ufw" "$out/python/ufw" "$out/bin" "$out/etc/default" "$out/etc/ufw/applications.d" "$out/share/ufw/iptables"
    cp src/*.py "$out/python/ufw/"
    touch "$out/python/ufw/__init__.py"
    cp src/ufw "$out/bin/ufw"
    cp src/ufw-init src/ufw-init-functions "$out/lib/ufw/"
    cp conf/*.rules conf/ufw.conf conf/sysctl.conf "$out/etc/ufw/"
    cp conf/ufw.defaults "$out/etc/default/ufw"
    cp profiles/* "$out/etc/ufw/applications.d/"
    cp conf/*.rules "$out/share/ufw/iptables/"
    for file in "$out"/python/ufw/*.py "$out"/bin/ufw "$out"/lib/ufw/* "$out"/etc/default/ufw "$out"/etc/ufw/*.*; do
      test -f "$file" || continue
      substituteInPlace "$file" \
        --replace-quiet '#CONFIG_PREFIX#' /etc \
        --replace-quiet '#STATE_PREFIX#' "$out/lib/ufw" \
        --replace-quiet '#SHARE_DIR#' "$out/share/ufw" \
        --replace-quiet '#PREFIX#' "$out" \
        --replace-quiet '#IPTABLES_DIR#' '${pkgs.iptables}/bin' \
        --replace-quiet '#VERSION#' 0.36.2
    done
    substituteInPlace "$out/lib/ufw/ufw-init-functions" \
      --replace-fail 'PATH="/sbin:/bin:/usr/sbin:/usr/bin"' 'PATH="${
        pkgs.lib.makeBinPath [
          pkgs.iptables
          pkgs.coreutils
          pkgs.gnugrep
          pkgs.gnused
          pkgs.gawk
          pkgs.procps
          pkgs.kmod
        ]
      }"'
    chmod +x "$out/bin/ufw" "$out/lib/ufw/ufw-init"
    patchShebangs "$out/bin" "$out/lib/ufw"
    makeWrapper ${pkgs.python3}/bin/python3 "$out/bin/ufw-fixture" \
      --add-flags "$out/bin/ufw" --set PYTHONPATH "$out/python" \
      --prefix PATH : ${
        pkgs.lib.makeBinPath [
          pkgs.iptables
          pkgs.procps
          pkgs.coreutils
          pkgs.gnugrep
          pkgs.gnused
          pkgs.kmod
        ]
      }
  ''
