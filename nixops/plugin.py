from nixops.plugins import NixOpsPlugin, hookimpl, MachineBackendRegistration, ResourceBackendRegistration
from nixops.backends.none import NoneState, NoneDefinition
from nixops.resources.commandOutput import CommandOutputDefinition, CommandOutputState
from nixops.resources.ssh_keypair import SSHKeyPairDefinition, SSHKeyPairState
from typing import List


class NixOpsCorePlugin(NixOpsPlugin):
    def machine_backends(self) -> List[MachineBackendRegistration]:
        return [
            MachineBackendRegistration(
                database_name="none",
                nix_name="none",
                definition_record=NoneDefinition,
                state_record=NoneState,
            )
        ]

    def resource_backends(self) -> List[ResourceBackendRegistration]:
        return [
            ResourceBackendRegistration(
                database_name="ssh-keypair",
                nix_name="sshKeyPairs",
                definition_record=SSHKeyPairDefinition,
                state_record=SSHKeyPairState,
            ),
            ResourceBackendRegistration(
                database_name="command-output",
                nix_name="commandOutput",
                definition_record=CommandOutputDefinition,
                state_record=CommandOutputState,
            ),
        ]


@hookimpl
def register_plugin() -> NixOpsPlugin:
    return NixOpsCorePlugin()
