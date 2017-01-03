# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys
import socket
import struct
import subprocess
from time import sleep
from pprint import pprint
import xml.etree.ElementTree as ET

from nixops.nix_expr import RawValue, Function, Call, nixmerge, py2nix
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
        self.setup_script = config['packet']['setup_script']

class PacketState(MachineState):
    """
    State of a Packet machine.
    """
    @classmethod
    def get_type(cls):
        return "packet"

    state = attr_property("state", MachineState.UNKNOWN, int)

    public_ipv4 = nixops.util.attr_property("publicIpv4", None)
    private_ipv4 = nixops.util.attr_property("privateIpv4", None)
    project_uuid = attr_property("packet.project", None)
    token = attr_property("packet.token", None)
    plan = attr_property("packet.plan", None)
    facility = attr_property("packet.facility", None)
    ssh_key = attr_property("packet.SSHKey", None)
    setup_script = attr_property("packet.setup_script", None)

    def __init__(self, depl, name, id):
        MachineState.__init__(self, depl, name, id)


    @property
    def resource_id(self):
        return self.vm_id

    def _vm_id(self):
        return "nixops-{0}-{1}".format(self.depl.uuid, self.name)


    def get_ssh_name(self):
        return self.public_ipv4

    def create_after(self, resources, defn):
        ret = [r for r in resources if
            isinstance(r, nixops.resources.packet_sshkey.PacketSSHKeyState)
        ]

        return ret

    def create(self, defn, check, allow_reboot, allow_recreate):
        self.set_common_state(defn)

        api_helper = nixops.resources.packet_sshkey.PacketAPIHelper(defn.token)
        api = api_helper.api_client_manager()

        if self.vm_id is None:
            self.log("Creating new Packet server")
            device = api.create_device(project_id=defn.project,
                                       hostname=self.name,
                                       plan=defn.plan,
                                       facility=defn.facility,
                                       operating_system='ubuntu_14_04')

            with self.depl._db:
                self.vm_id = device.id
                self.ssh_key = defn.ssh_key
        else:
            self.log("Found existing Packet server with ID {0}".format(self.vm_id))


        ticker = 0
        while True:
            try:
                device = api.get_device(self.vm_id)
                if device.state == "provisioning":
                    ticker += 1
                    if ticker == 30:
                        self.log("Still provisioning...")
                        ticker = 0
                elif device.state == "active":
                       self.log("Server now active")
                       break
                sleep(1)
            except packet.baseapi.Error as e:
                with self.depl._db:
                    self.state = self.MISSING
                    self.vm_id = None
                return

        pprint(self.get_ssh_private_key_file())
        # pprint(self.get_ssh_public_key_file())

        with self.depl._db:
            for ip in device.ip_addresses:
                if ip['address_family'] == 4:
                    if ip['public']:
                        self.public_ipv4 = ip['address']
                    else:
                        self.private_ipv4 = ip['address']

        self.wait_for_ssh()
        self.run_command('pwd')

        #self.send_kexec()
        #self.run_command('cd /; tar -xf /root/kexec.tar.xz')
        read, write = os.pipe()
        os.write(write, """#!/bin/sh
          cd /
          (./kexec_nixos > /dev/null 2>&1 &) &
        """)
        os.close(write)

        self.run_command('cat > /root/kexec.sh', stdin=read)
        self.run_command('chmod +x /root/kexec.sh')
        self.run_command('/root/kexec.sh')
        while True:
            self.wait_for_ssh()
            try:
                pprint(self.run_command('[ `hostname` = "kexec" ]'))
                break
            except nixops.ssh_util.SSHCommandFailed as e:
                sleep(1)

        self.log("OHI NIXOS!")

        read, write = os.pipe()
        os.write(write, """#!/bin/sh
          {0}
        """.format(defn.setup_script))
        os.close(write)
        self.run_command('cat > /root/setup.sh', stdin=read)

        print(self.depl.get_physical_spec())
        #print py2nix(defn.config)
        sleep(600)
        assert False
        return True

    def send_kexec(self):
        self.log_start("copying bootstrap files to rescue system... ")
        expr = os.path.join(self.depl.expr_path, "kexec.nix")
        bootstrap_out = subprocess.check_output(["nix-build", expr,
                                                 "--no-out-link"]).rstrip()
        bootstrap = os.path.join(bootstrap_out, 'tarball/nixos-system-x86_64-linux.tar.xz')
        if not self.has_fast_connection:
            stream = subprocess.Popen(["gzip", "-c"], stdin=open(bootstrap),
                                      stdout=subprocess.PIPE)
            self.run_command("gzip -d > /root/kexec.tar.xz".format(),
                             stdin=stream.stdout)
            stream.wait()
        else:
            self.run_command('cat > /root/kexec.tar.xz', stdin=open(bootstrap))


        self.log_end("done.")


    def destroy(self, wipe):
        if wipe:
            log.warn("Wipe is not supported")

        return True

    def get_ssh_private_key_file(self):
        for r in self.depl.active_resources.itervalues():
            if isinstance(r, nixops.resources.packet_sshkey.PacketSSHKeyState) and \
               r.state == nixops.resources.packet_sshkey.PacketSSHKeyState.UP and \
               r.keypair_name == self.ssh_key:
                return self.write_ssh_private_key(r.private_key)

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
