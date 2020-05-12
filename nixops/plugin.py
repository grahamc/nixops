from nixops.plugins import (
    NixOpsPlugin,
    hookimpl,
    MachineBackendRegistration,
    ResourceBackendRegistration,
)
from nixops.backends import MachineState
from nixops.resources import ResourceState
from nixops.backends.none import NoneState, NoneDefinition
from nixops.resources.commandOutput import CommandOutputDefinition, CommandOutputState
from nixops.resources.ssh_keypair import SSHKeyPairDefinition, SSHKeyPairState
from typing import List, Type


class NixOpsCorePlugin(NixOpsPlugin):
    def machine_backends(self) -> List[Type[MachineState]]:
        return [NoneState]

    def resource_backends(self) -> List[Type[ResourceState]]:
        return [SSHKeyPairState, CommandOutputState]


@hookimpl
def register_plugin() -> NixOpsPlugin:
    return NixOpsCorePlugin()
