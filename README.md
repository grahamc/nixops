# NixOps

NixOps (formerly known as Charon) is a tool for deploying NixOS
machines in a network or cloud.

* [Manual](https://nixos.org/nixops/manual/)
* [Installation](https://nixos.org/nixops/manual/#chap-installation) / [Hacking](https://nixos.org/nixops/manual/#chap-hacking)
* [Continuous build](http://hydra.nixos.org/jobset/nixops/master#tabs-jobs)
* [Source code](https://github.com/NixOS/nixops)
* [Issue Tracker](https://github.com/NixOS/nixops/issues)
* [Mailing list / Google group](https://groups.google.com/forum/#!forum/nixops-users)
* [IRC - #nixos on freenode.net](irc://irc.freenode.net/#nixos)


---

```
plugin$ nix-shell
- mutable plugin source, immutable nixops src
- mypy works
- tests work
- `nixops` works, using this plugin


nixops$ nix-shell
OK - no plugins
OK - mutable nixops src
OK - mypy works
OK - tests work

nixops$ nix-shell --arg plugin ../plugin
- mutable plugin, mutable nixops
- mypy checks both plugin and nixops
- tests checks both plugin and nixops
- `nixops` works including the plugin

nixops$ nix-shell --arg plugins "[ ../plugin1 ../plugin2 ../plugin3 ]"
- mutable plugins, mutable nixops
- mypy checks all plugins and nixops
- tests checks all plugins and nixops
- `nixops` works including the plugins

plugin$ nix-build
- runs mypy
- runs tests
- produces artifact which can be passed in to a nixops build
- build result is NOT a working nixops

nixops$ nix-build
- runs mypy
- runs tests
- produces nixops which is functional, but without any plugins

nixops$ nix-build --arg plugin ../plugin
- runs mypy checks both plugin and nixops
- runs tests checks both plugin and nixops
- build result is a `nixops` works including the plugin

nixops$ nix-build --arg plugins "[ ../plugin1 ../plugin2 ../plugin3 ]"
- runs mypy checks all plugins and nixops
- runs tests checks all plugins and nixops
- build result is a `nixops` works including the plugins
```


---

## Developing

To start developing on nixops, you can run:

```bash
  $ ./dev-shell --arg p "(p: [ p.plugin1 ])"
```

Where plugin1 can be any available nixops plugin, and where
none or more than one can be specified, including local plugins.
An example is:


```bash
  $ ./dev-shell --arg p "(p: [ p.aws p.hetzner (p.callPackage ../myplugin/release.nix {})])"
```

Available plugins, such as "aws" and "hetzner" in the example
above, are the plugin attribute names found in the data.nix file.

To update the available nixops plugins found in github repositories,
edit the all-plugins.txt file with any new github plugin repositories
that are available and then execute the update-all script.  This will
refresh the data.nix file, providing new plugin attributes to use.

Local nixops plugins, such as the `callPackage ../myplugin/release.nix {}`
example seen above, have no need to be in the all-plugins.txt
or data.nix file.

## Building from source

The command to build NixOps depends on your platform and which plugins you choose:

- `nix-build release.nix -A build.x86_64-linux --arg p "(p: [ p.plugin1 ])"` on 64 bit linux.
- `nix-build release.nix -A build.i686-linux --arg p "(p: [ p.plugin1 ])"` on 32 bit linux.
- `nix-build release.nix -A build.x86_64-darwin --arg p "(p: [ p.plugin1 ])"` on OSX.

Similarly, using NixOps from another project (for instance a nix-shell) can be done using:

```nix
stdenv.mkDerivation {
  name = "my-nixops-env";
  buildInputs = [
    (import /path/to/nixops/release.nix { p = (p: [ p.plugin1 ]); }).build.x86_64-linux
  ];
}
```
