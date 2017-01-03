{ config, pkgs, lib, utils, ... }:

with utils;
with import ./lib.nix lib;
with lib;

{
  ###### interface

  options.deployment.packet = {
    project = mkOption {
      type = types.str;
      description = ''
        Your project's UUID
      '';
    };

    token = mkOption {
      type = types.str;
      description = ''
        API Token for your Packet.net account.
      '';
    };

    plan = mkOption {
      default = "baremetal_1";
      type = types.str;
      description = ''
        Plan (ie: Type of server)
      '';
    };

    facility  = mkOption {
      default = "ewr1";
      type = types.str;
      description = ''
        Datacenter
      '';
    };

    SSHKey = mkOption {
      type = types.either types.str (resource "packet-keypair");
      apply = x: if builtins.isString x then x else x.name;
      description = ''
        Packet SSH Key
      '';
    };

    setup_script = mkOption {
      type = types.lines;
      description = ''
        Formatting, partitioning, and mounting commands... :)
      '';
    };

  };

  ###### implementation

  config = mkIf (config.deployment.targetEnv == "packet") {
    nixpkgs.system = mkOverride 900 "x86_64-linux";
    boot.loader.grub.version = 2;
    boot.loader.timeout = 1;
    services.openssh.enable = true;

    security.initialRootPassword = mkDefault "!";
  };
}
