{
  description = "NixOps: a tool for deploying to [NixOS](https://nixos.org) machines in a network or the cloud";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  inputs.utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, utils }: utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs { inherit system; };

    pythonEnv = (pkgs.poetry2nix.mkPoetryEnv {
      projectDir = ./.;
    });
    linters.doc = pkgs.writers.writeBashBin "lint-docs" ''
      set -eux
      # When running it in the Nix sandbox, there is no git repository
      # but sources are filtered.
      if [ -d .git ];
      then
          FILES=$(${pkgs.git}/bin/git ls-files)
      else
          FILES=$(find .)
      fi
      echo "$FILES" | xargs ${pkgs.codespell}/bin/codespell -L keypair,iam,hda
      ${pythonEnv}/bin/sphinx-build -M clean doc/ doc/_build
      ${pythonEnv}/bin/sphinx-build -n doc/ doc/_build
      '';

  in {
    devShell = pkgs.mkShell {
      buildInputs = [
        pythonEnv
        pkgs.openssh
        pkgs.poetry
        pkgs.rsync  # Included by default on NixOS
        pkgs.nixFlakes
        pkgs.codespell
      ] ++ (builtins.attrValues linters);

      shellHook = ''
        git_root=$(${pkgs.git}/bin/git rev-parse --show-toplevel)
        export PYTHONPATH=$git_root:$PYTHONPATH
        export PATH=$git_root/scripts:$PATH
      '';
    };

    defaultPackage = let
      overrides = import ./overrides.nix { inherit pkgs; };

    in pkgs.poetry2nix.mkPoetryApplication {
      projectDir = ./.;

      propagatedBuildInputs = [
        pkgs.openssh
        pkgs.rsync
      ];

      overrides = [
        pkgs.poetry2nix.defaultPoetryOverrides
        overrides
      ];

      # TODO: Re-add manual build
    };

    checks.doc = pkgs.stdenv.mkDerivation {
      name = "lint-docs";
      # we use cleanPythonSources because the default gitignore
      # implementation doesn't support the restricted evaluation
      src = pkgs.poetry2nix.cleanPythonSources {
        src = ./.;
      };
      dontBuild = true;
      installPhase = ''
        ${linters.doc}/bin/lint-docs | tee $out
      '';
    };
  });
}
