# -*- coding: utf-8 -*-

# Automatic provisioning of Packet SSH Key Pairs.

import nixops.util
import nixops.resources
from pprint import pprint

class PacketAPIHelper:
    def __init__(token):
        self.token = token
        self._api_client_manager = None

    def api_client_manager(self):
        if self._api_client_manager is None:
            self._api_client_manager = packet.Manager(
                auth_token=self.token
            )
        return self._api_client_manager

    def ssh_key_by_label(self, label):
        current = api.list_ssh_keys()
        for key in current:
            if key.label == label:
                return found_key
        return None


class PacketSSHKeyDefinition(nixops.resources.ResourceDefinition):
    """Definition of an Packet SSH key pair."""

    @classmethod
    def get_type(cls):
        return "packet-keypair"

    @classmethod
    def get_resource_type(cls):
        return "packetSSHKeys"

    def __init__(self, xml, config):
        pprint("init key def")
        nixops.resources.ResourceDefinition.__init__(self, xml)
        self.keypair_name = xml.find("attrs/attr[@name='name']/string").get("value")
        self.token = xml.find("attrs/attr[@name='token']/string").get("value")



class PacketSSHKeyState(nixops.resources.ResourceState):
    """State of an Packet SSH key pair."""

    state = nixops.util.attr_property("state", nixops.resources.ResourceState.MISSING, int)
    keypair_name = nixops.util.attr_property("name", None)
    public_key = nixops.util.attr_property("publicKey", None)
    private_key = nixops.util.attr_property("privateKey", None)
    token = nixops.util.attr_property("token", None)


    @classmethod
    def get_type(cls):
        return "packet-keypair"

    def __init__(self, depl, name, id):
        pprint("Init key state")
        nixops.resources.ResourceState.__init__(self, depl, name, id)
        pprint(self.state)

    @property
    def resource_id(self):
        return self.keypair_name


    def get_definition_prefix(self):
        return "resources.packetSSHKeys."


    def create(self, defn, check, allow_reboot, allow_recreate):
        pprint("hi there")
        # Generate the key pair locally.
        if not self.public_key:
            self.log("Creating keypair...")
            (private, public) = nixops.util.create_key_pair()
            with self.depl._db:
                self.public_key = public
                self.private_key = private
        else:
            self.log("Don't need to create keypair, since it has been done already...")

        # Upload the public key to Packet
        if check or self.state != self.UP:
            api_helper = PacketAPIHelper(defn.token)
            api = api_heler.api_client_manager()
            key = api_helper.ssh_key_by_label(defn.keypair_name)

            if key is not None or self.state != self.UP:
                if key is not None:
                    self.log("deleting Packet SSH Key '{0}' before creating...".format(
                        defn.keypair_name
                    ))
                    key.delete()

                self.log("uploading Packet SSH Key '{0}'...".format(
                    defn.keypair_name
                ))
                api.create_ssh_key(defn.keypair_name, self.public_key)
            else:
                self.log("Key was already created and uploaded.")

            with self.depl._db:
                self.state = self.UP
                self.keypair_name = defn.keypair_name
                self.log("Updated DB")

    def destroy(self, wipe=False):
        if self.state == self.UP:
            self.log("deleting Packet SSH key pair ‘{0}’...".format(self.keypair_name))
            key = defn
            self._conn.delete_key_pair(self.keypair_name)

        return True
