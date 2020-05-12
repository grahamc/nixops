import pluggy
from pathlib import Path
from typing import Type, List
from typing_extensions import Protocol
from nixops.resources import ResourceDefinition, ResourceState
from nixops.backends import MachineDefinition, MachineState

hookspec = pluggy.HookspecMarker("nixops")


class MachineBackendRegistration:
    # get_type          -> how it is stored in the database
    # get_resource_type -> `resources.«name».options`
    database_name: str
    nix_name: str
    definition_record: Type[MachineDefinition]
    state_record: Type[MachineState]


class ResourceBackendRegistration:
    # get_type          -> how it is stored in the database
    # get_resource_type -> `resources.«name».options`
    database_name: str
    nix_name: str
    definition_record: Type[ResourceDefinition]
    state_record: Type[ResourceState]


class NixOpsPlugin(Protocol):
    def machine_backends(self) -> List[MachineBackendRegistration]:
        pass

    def resource_backends(self) -> List[ResourceBackendRegistration]:
        pass

    def nix_expression_files(self) -> List[Path]:
        pass

    def cli_extension(self, parser, subparsers):
        pass


@hookspec
def register_plugin() -> NixOpsPlugin:
    """ Register my plugin
    """
