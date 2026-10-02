{ pkgs }:
pkgs.runCommand "home-source-assets"
  {
    nativeBuildInputs = [
      pkgs.bash
      pkgs.nodejs
      pkgs.jq
      pkgs.findutils
      pkgs.gnused
      pkgs.qt6.qtdeclarative
    ];
  }
  ''
    find ${../files/home}/.config -name '*.json' -exec jq empty {} +
    find ${../files/home}/.config/quickshell/overview -name '*.qml' -exec qmlformat {} + >/dev/null 2>&1
    find ${../files/home}/.agents/skills -name '*.sh' -exec bash -n {} +
    find ${../files/home}/.config/quickshell -name '*.js' | while read -r file; do
      sed 's/^\.pragma library$//' "$file" | node --check >/dev/null
    done
    echo "Tracked JSON, overview QML, skill shell syntax and JavaScript syntax passed."
    touch "$out"
  ''
