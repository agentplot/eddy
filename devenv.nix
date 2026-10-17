{
  pkgs,
  lib,
  config,
  ...
}:

let
  # A tool's own release builds: nixpkgs trails proto by minor versions or
  # more. Linux takes the static musl build, so no loader needs patching.
  fromRelease =
    {
      name,
      repo,
      version,
      bins,
      hashes,
    }:
    let
      system = pkgs.stdenv.hostPlatform.system;
      target =
        {
          aarch64-darwin = "aarch64-apple-darwin";
          x86_64-darwin = "x86_64-apple-darwin";
          aarch64-linux = "aarch64-unknown-linux-musl";
          x86_64-linux = "x86_64-unknown-linux-musl";
        }
        .${system} or (throw "${name} ${version}: no release build for ${system}");
    in
    pkgs.stdenvNoCC.mkDerivation {
      pname = name;
      inherit version;
      src = pkgs.fetchurl {
        url = "https://github.com/${repo}/releases/download/v${version}/${name}-${target}.tar.xz";
        sha256 = hashes.${target};
      };
      sourceRoot = "${name}-${target}";
      installPhase = ''
        runHook preInstall
        install -Dm755 -t $out/bin ${pkgs.lib.concatStringsSep " " bins}
        runHook postInstall
      '';
    };

  proto = fromRelease {
    name = "proto_cli";
    repo = "moonrepo/proto";
    version = "0.63.1";
    bins = [
      "proto"
      "proto-shim"
    ];
    hashes = {
      aarch64-apple-darwin = "8bfde4c862381eeb6e82d0858bb6215732cbd1e384e4eae45da8fa08095e0ffd";
      x86_64-apple-darwin = "aaaff78c7125de1b765f00177f35da75ee16fb1363e07632ace27213ff5d893b";
      aarch64-unknown-linux-musl = "111f5b6a38d3979ebafbc095c8d91ef69c99d1f018addb3582179d4ab91b3441";
      x86_64-unknown-linux-musl = "8596b98ccd833d1203e71931ba25e866d3239f9d3859c922a035a7b830f29d17";
    };
  };

  # The application toolchain .prototools pins, on PATH: what the shell
  # activates. proto's home is this repository's, in the git common dir so
  # every worktree shares it: moon puts $PROTO_HOME/bin on every task's
  # PATH, and the user's own proto installs must never shadow the system
  # tools above. Only this repository's pins are read.
  protoHome = ''
    PROTO_HOME="$(${lib.getExe pkgs.git} rev-parse --path-format=absolute --git-common-dir)/proto"
    export PROTO_HOME
  '';
  activate = ''
    ${protoHome}
    eval "$(${proto}/bin/proto activate bash --export --no-bin --config-mode upwards 2>/dev/null)"
  '';

  # Vale checks the site's prose (.vale.ini, styles/Eddy). From its own
  # release: nixpkgs trails it. Bump the version and the four hashes from
  # the release's checksums file.
  valeVersion = "3.24.0";
  valeAssets = {
    aarch64-darwin = {
      os = "macOS_arm64";
      sha256 = "87b513f26499f6657c15cf7175ba5b058a7c1ff2bb2d4e07265db2dd43451e44";
    };
    x86_64-darwin = {
      os = "macOS_64-bit";
      sha256 = "eeb39e86f1daac27cc2a77fef3af1824d50559bdc22329fb25fb921c80c79472";
    };
    aarch64-linux = {
      os = "Linux_arm64";
      sha256 = "104cbd349279e50c4cb40adb70adf345d93cc4a3a0191f9e68bdccb97086b582";
    };
    x86_64-linux = {
      os = "Linux_64-bit";
      sha256 = "867534ddb678abca7f214bc4706ead0922bd5252ffe8035fc227013f66c8b214";
    };
  };
  valeAsset = valeAssets.${pkgs.stdenv.hostPlatform.system};
  vale = pkgs.stdenvNoCC.mkDerivation {
    pname = "vale";
    version = valeVersion;
    src = pkgs.fetchurl {
      url = "https://github.com/errata-ai/vale/releases/download/v${valeVersion}/vale_${valeVersion}_${valeAsset.os}.tar.gz";
      inherit (valeAsset) sha256;
    };
    sourceRoot = ".";
    installPhase = "install -Dm755 vale $out/bin/vale";
  };

in
{
  # The system tools are this file's, pinned by devenv.lock; the application
  # tools (moon) are .prototools', installed by the eddy:proto:install task
  # on entering the shell and activated by enterShell.
  packages = [
    pkgs.git
    pkgs.jq
    pkgs.python3
    proto
    vale
    # The site (site/): bun builds it, and Playwright with the one browser
    # it drives, from Nix, screenshots its pages (site/scripts/shots.mjs).
    pkgs.bun
    pkgs.playwright-test
  ];

  env.PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers-chromium}";

  # moon's task archives (.moon/cache/outputs) are a link into the git common
  # dir, so every worktree of eddy shares them. The rest of .moon/cache
  # records the checkout's absolute paths and stays its own. The worktree is
  # found when the shell is entered, never written in at evaluation.
  enterShell = ''
    if _moon_root="$(git rev-parse --show-toplevel 2>/dev/null)" &&
      _moon_common="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
      _moon_cache="$_moon_root/.moon/cache"
      [ -L "$_moon_cache" ] && rm -f "$_moon_cache"
      mkdir -p "$_moon_common/moon-outputs" "$_moon_cache"
      if [ ! -L "$_moon_cache/outputs" ]; then
        rm -rf "$_moon_cache/outputs"
        ln -s "$_moon_common/moon-outputs" "$_moon_cache/outputs"
      fi
      # moon puts $MOON_HOME/bin on every task's PATH too: this repository's,
      # beside proto's, so no moon of the user's runs in a task.
      MOON_HOME="$_moon_common/moon-home"
      export MOON_HOME
    fi
    unset _moon_root _moon_common _moon_cache
    ${activate}
  '';

  # The tool versions .prototools lists, installed on entering the shell,
  # before enterShell activates them. A task, not part of enterShell: the
  # script `devenv print-dev-env` prints holds enterShell and none of the
  # tasks, so a check run sourcing it never installs.
  tasks."eddy:proto:install" = {
    exec = ''
      ${protoHome}
      ${proto}/bin/proto install --config-mode upwards
    '';
    before = [ "devenv:enterShell" ];
  };

  treefmt.enable = true;
  treefmt.config = {
    imports = [ ./treefmt.nix ];
    # The tree is found from where treefmt runs, by this file, rather than
    # devenv's evaluated root written into the wrapper.
    projectRootFile = "devenv.nix";
  };

  scripts.prose = {
    description = "The site's prose, checked by Vale (.vale.ini)";
    exec = ''
      set -euo pipefail
      cd "$(git rev-parse --show-toplevel)"
      vale site/src/content/docs "$@"
    '';
  };
  scripts.diagrams = {
    description = "The diagrams the README and the book show, written to docs/diagrams";
    exec = ''
      set -euo pipefail
      cd "$(git rev-parse --show-toplevel)"
      python3 docs/diagrams/diagrams.py docs/diagrams "$@"
    '';
  };

  # The floor under every commit, installed into the common hooks directory
  # on `devenv shell`. convco refuses a message that is not a conventional
  # commit (.versionrc), since git-cliff releases from them.
  git-hooks.hooks = {
    convco = {
      enable = true;
      settings.configPath = ".versionrc";
    };
    treefmt.enable = true;
  };

  # devenv 2.4 installs the hook with `prek install -c
  # "$DEVENV_ROOT/.pre-commit-config.yaml"`, and prek writes that absolute
  # path into the hook, which lives in the hooks directory every worktree
  # shares. A plain `prek install` writes no path, and prek reads the
  # config at the top of the worktree the commit is in, which devenv links
  # there. Remove this once devenv installs without the absolute path
  # (cachix/devenv#3270).
  tasks."devenv:git-hooks:install".exec = lib.mkForce ''
    set -euo pipefail
    hooks="$(${lib.getExe pkgs.git} rev-parse --path-format=absolute --git-path hooks)"
    for type in pre-commit commit-msg; do
      if ! grep -q 'File generated by prek' "$hooks/$type" 2>/dev/null || grep -q -- '--config=' "$hooks/$type"; then
        ${lib.getExe config.git-hooks.package} install --force -t "$type"
      fi
    done
  '';
}
