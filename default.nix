{ pkgs ? import <nixpkgs> {} }:
let
  overrides = import ./overrides.nix { inherit pkgs; };

in pkgs.poetry2nix.mkPoetryApplication {
  projectDir = ./.;
  src = ./.;
  pyproject = ./pyproject.toml;
  poetrylock = ./poetry.lock;


  propagatedBuildInputs = [
    pkgs.openssh
  ];

  overrides = [
    overrides
  ];
}
