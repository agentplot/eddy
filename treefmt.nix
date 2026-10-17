_: {
  settings.excludes = [
    "*.md"
    "*.mdx"
    "*.lock"
    "*.json"
    "*.svg"
    "site/**"
    ".devenv/**"
    ".moon/cache/**"
  ];

  programs.deadnix.enable = true;
  programs.nixfmt.enable = true;
  settings.formatter.deadnix.pipeline = "nix";
  settings.formatter.deadnix.priority = 1;
  settings.formatter.nixfmt.pipeline = "nix";
  settings.formatter.nixfmt.priority = 2;

  programs.taplo.enable = true;
  programs.yamlfmt.enable = true;
  programs.yamlfmt.settings.formatter = {
    type = "basic";
    retain_line_breaks_single = true;
  };
}
