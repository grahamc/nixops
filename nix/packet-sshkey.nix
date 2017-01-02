{ config, lib, uuid, name, ... }:

with lib;

{

  options = {

    name = mkOption {
      default = "nixops-${uuid}-${name}";
      type = types.str;
      description = "Name of the Packet SSH key.";
    };

    token = mkOption {
      type = types.str;
      description = "API Token.";
    };
  };

  config._type = "packet-keypair";

}
