{
  config,
  lib,
  pkgs,
  ...
}:
{
  home.sessionPath = [
    "$HOME/.local/bin"
    "$HOME/go/bin"
    "$HOME/.luarocks/bin"
  ];

  home.packages = with pkgs; [
    bat
    bc
    btop
    cava
    chafa
    curl
    eza
    fastfetch
    fd
    gum
    jq
    just
    lsd
    p7zip
    ripgrep
    rsync
    tldr
    unzip
    wget
  ];

  programs = {
    fzf = {
      enable = true;
      enableZshIntegration = true;
    };

    git = {
      enable = true;
      settings = {
        core = {
          autocrlf = false;
          filemode = false;
          fsmonitor = false;
          ignorecase = true;
          longpaths = true;
          quotePath = false;
          symlinks = true;
        };
        diff.algorithm = "histogram";
        fetch.prune = true;
        init.defaultBranch = "main";
        merge.conflictStyle = "zdiff3";
        pull.rebase = true;
        rebase.autoStash = true;
      };
    };

    zsh = {
      enable = true;
      autosuggestion.enable = true;
      enableCompletion = true;
      syntaxHighlighting.enable = true;
      history = {
        expireDuplicatesFirst = true;
        ignoreAllDups = true;
        ignoreDups = true;
        ignoreSpace = true;
        save = 10000;
        share = true;
        size = 10000;
      };
      shellAliases = {
        l = "lsd -l";
        la = "lsd -a";
        ll = "lsd -al";
        lt = "lsd --tree";
        v = "nvim";
      };
      oh-my-zsh = {
        enable = true;
        plugins = [ "git" ];
      };
      initContent = lib.mkOrder 1000 ''
        source ${pkgs.zsh-powerlevel10k}/share/zsh-powerlevel10k/powerlevel10k.zsh-theme
        [[ -r ${config.home.homeDirectory}/.p10k.zsh ]] && source ${config.home.homeDirectory}/.p10k.zsh
        bindkey '^K' autosuggest-accept
      '';
    };
  };
}
