# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys
import socket
import struct
import subprocess
from pprint import pprint
import xml.etree.ElementTree as ET


from nixops import known_hosts
from nixops.util import wait_for_tcp_port, ping_tcp_port
from nixops.util import attr_property, create_key_pair
from nixops.ssh_util import SSHCommandFailed
from nixops.backends import MachineDefinition, MachineState
from nixops.nix_expr import nix2py
import nixops.resources.packet_sshkey


import packet


class PacketDefinition(MachineDefinition):
    """
    Definition of a Packet machine.
    """
    @classmethod
    def get_type(cls):
        return "packet"

    def __init__(self, xml, config):
        MachineDefinition.__init__(self, xml, config)
        self.project = config['packet']['project']
        self.token = config['packet']['token']
        self.plan = config['packet']['plan']
        self.facility = config['packet']['facility']
        self.ssh_key = config['packet']['SSHKey']

class PacketState(MachineState):
    """
    State of a Packet machine.
    """
    @classmethod
    def get_type(cls):
        return "packet"

    state = attr_property("state", MachineState.UNKNOWN, int)

    project_uuid = attr_property("packet.project", None)
    token = attr_property("packet.token", None)
    plan = attr_property("packet.plan", None)
    facility = attr_property("packet.facility", None)
    ssh_key = attr_property("packet.SSHKey", None)

    def __init__(self, depl, name, id):
        MachineState.__init__(self, depl, name, id)

    @property
    def resource_id(self):
        return self.vm_id

    @property
    def public_ipv4(self):
        return self.main_ipv4

    def _vm_id(self):
        return "nixops-{0}-{1}".format(self.depl.uuid, self.name)


    def create_after(self, resources, defn):
        return {r for r in resources if
            isinstance(r, nixops.resources.packet_sshkey.PacketSSHKeyState)
        }

    def create(self, defn, check, allow_reboot, allow_recreate):
        self.log("Creating new Packet server")
        self.set_common_state(defn)

        pprint(defn.ssh_key)

        ssh_key = self.depl.active_resources.get(defn.ssh_key)
        if ssh_key is None:
            raise Exception('Please specify an SSH key!')

    def get_ssh_private_key_file(self):
        for r in self.depl.active_resources.itervalues():
            if isinstance(r, nixops.resources.packet_sshkey.PacketSSHKeyState) and \
               r.state == nixops.resources.packet_sshkey.PacketSSHKeyState.UP and \
               r.name == self.ssh_key:
                return self.write_ssh_private_key(r.private_Key)

    def get_ssh_flags(self, *args, **kwargs):
        return super(PacketState, self).get_ssh_flags(*args, **kwargs) + (
            ["-o", "LogLevel=quiet",
             "-o", "UserKnownHostsFile=/dev/null",
             "-o", "GlobalKnownHostsFile=/dev/null",
             "-o", "StrictHostKeyChecking=no"]
            if self.state == self.RESCUE else
            # XXX: Disabling strict host key checking will only impact the
            # behaviour on *new* keys, so it should be "reasonably" safe to do
            # this until we have a better way of managing host keys in
            # ssh_util. So far this at least avoids to accept every damn host
            # key on a large deployment.
            ["-o", "StrictHostKeyChecking=no",
             "-i", self.get_ssh_private_key_file()]
        )
