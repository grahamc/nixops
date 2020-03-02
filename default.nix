{ nixopsSrc ? { outPath = ./.; revCount = 0; shortRev = "abcdef"; rev = "HEAD"; }
, officialRelease ? false
, pkgs ? import <nixpkgs> {}
, p ? (p: [ ])
}:

let
  version = "1.8" + (if officialRelease then "" else "pre${toString nixopsSrc.revCount}_${nixopsSrc.shortRev}");
  pythonPackages = pkgs.python37Packages;
in pythonPackages.buildPythonApplication rec {
  name = "nixops-${version}";

  src = ./.;

  buildInputs = [
    pythonPackages.nose
    pythonPackages.coverage
  ];

  nativeBuildInputs = [
    pkgs.libxslt
    pkgs.docbook5_xsl
    (pythonPackages.mypy.overrideAttrs ({ propagatedBuildInputs, ... }: {
      propagatedBuildInputs = propagatedBuildInputs ++ [
        pythonPackages.lxml
      ];
    }))
    pythonPackages.black
  ];

  propagatedBuildInputs = [
    pythonPackages.prettytable
    pythonPackages.pluggy
  ];

  preBuild = ''
    cp ${(import ./doc/manual { revision = nixopsSrc.rev; nixpkgs = pkgs.path; }).optionsDocBook} doc/manual/machine-options.xml
    for i in scripts/nixops setup.py doc/manual/manual.xml; do
      substituteInPlace $i --subst-var-by version ${version}
    done
  '';

  # For "nix-build --run-env".
  shellHook = ''
    export PYTHONPATH=$(pwd):$PYTHONPATH
    export PATH=$(pwd)/scripts:${pkgs.openssh}/bin:$PATH
  '';

  doCheck = true;

  postCheck = ''
    mypy nixops

    # smoke test
    HOME=$TMPDIR $out/bin/nixops --version
  '';

  # Needed by libcloud during tests
  SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";

  # Add openssh to nixops' PATH. On some platforms, e.g. CentOS and RHEL
  # the version of openssh is causing errors when have big networks (40+)
  makeWrapperArgs = ["--prefix" "PATH" ":" "${pkgs.openssh}/bin" "--set" "PYTHONPATH" ":"];

  postInstall = ''
    # Backward compatibility symlink.
    ln -s nixops $out/bin/charon

    make -C doc/manual install \
    docdir=$out/share/doc/nixops mandir=$out/share/man

    mkdir -p $out/share/nix/nixops
    cp -av nix/* $out/share/nix/nixops
  '';

  meta.description = "Nix package for ${pkgs.stdenv.system}";
}
