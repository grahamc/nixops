{ nixos ? import <nixpkgs/nixos> }:
(nixos {
  configuration = { lib, pkgs, config, ... }:
  let
    image = pkgs.runCommand "image" { buildInputs = [ pkgs.nukeReferences ]; } ''
      mkdir $out
      cp ${config.system.build.kernel}/bzImage $out/kernel
      cp ${config.system.build.netbootRamdisk}/initrd $out/initrd
      nuke-refs $out/kernel
    '';
  in {
    imports = [ <nixpkgs/nixos/modules/installer/netboot/netboot-minimal.nix> ];
    system.build.kexec_script = pkgs.writeTextFile {
      executable = true;
      name = "kexec-nixos";
      text = ''
        #!${pkgs.stdenv.shell}
        export PATH=${pkgs.kexectoolsFixed}/bin:${pkgs.cpio}/bin:$PATH
        set -x
        cd $(mktemp -d)
        pwd
        mkdir initrd
        pushd initrd
        cp /root/.ssh/authorized_keys ./authorized_keys
        find -type f | cpio -o -H newc | gzip -9 > ../extra.gz
        popd
        cat ${image}/initrd extra.gz > final.gz
        kexec -l ${image}/kernel --initrd=final.gz --append="init=${builtins.unsafeDiscardStringContext config.system.build.toplevel}/init ${toString config.boot.kernelParams}"
        sync
        echo "executing kernel, filesystems will be improperly umounted"
        kexec -e
      '';
    };
    boot.initrd.postMountCommands = ''
      mkdir -p /mnt-root/root/.ssh/
      cp /authorized_keys /mnt-root/root/.ssh/
    '';

    system.build.kexec_tarball = pkgs.callPackage <nixpkgs/nixos/lib/make-system-tarball.nix> {
      storeContents = [
        { object = config.system.build.kexec_script; symlink = "/kexec_nixos"; }
      ];
      contents = [];
    };
    boot.loader.grub.enable = false;
    boot.kernelParams = [ "console=ttyS0,115200" ];
    systemd.services.sshd.wantedBy = lib.mkForce [ "multi-user.target" ];
    networking.hostName = "kexec";
    nixpkgs.config.packageOverrides = pkgs: {
      kexectoolsFixed = pkgs.kexectools.overrideDerivation (old: {
        hardeningDisable = [ "all" ];
      });
    };
  };
}).config.system.build.kexec_tarball
