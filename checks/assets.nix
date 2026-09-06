{ pkgs }:
pkgs.runCommand "home-source-assets"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.bash
      pkgs.nodejs
    ];
  }
  ''
    python ${./tests/test_assets.py} ${../files/home} ${pkgs.qt6.qtdeclarative}/bin/qmlformat
    touch "$out"
  ''
