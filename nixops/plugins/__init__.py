import pluggy
from . import hookspecs
from typing import List, Mapping, Dict, Optional, Union, Set, Type
from nixops.resources import ResourceState, ResourceDefinition
from nixops.backends import MachineState, MachineDefinition
from .hookspecs import (
    NixOpsPlugin,
    MachineBackendRegistration,
    ResourceBackendRegistration,
)
from pathlib import Path
from argparse import ArgumentParser, _SubParsersAction

hookimpl = pluggy.HookimplMarker("nixops")
"""Marker to be imported and used in plugins (and for own implementations)"""


def _get_plugin_pm():
    import nixops.plugin

    pm = pluggy.PluginManager("nixops")
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints("nixops")
    pm.register(nixops.plugin)
    return pm


class NixOpsFeatureful:
    def __init__(self) -> None:
        self.pm = _get_plugin_pm()

        self.machine_backend_defns: Dict[str, Type[MachineDefinition]] = {}
        self.machine_backend_states: Dict[str, Type[MachineState]] = {}

        self.resource_backend_defns: Dict[str, Type[ResourceDefinition]] = {}
        self.resource_backend_states: Dict[str, Type[ResourceState]] = {}

        self._nix_expressions: Set[Path] = set()

        self._plugins: List[NixOpsPlugin] = []

        for plugin in self.pm.hook.register_plugin():
            self._plugins.append(plugin)
            # todo: verify that all the nix names and database names are unique across machine and resource backends

            self._nix_expressions.update(plugin.nix_expression_files())

            for machine_backend in plugin.machine_backends():
                self.machine_backend_defns[
                    machine_backend.nix_name
                ] = machine_backend.definition_record
                self.machine_backend_states[
                    machine_backend.database_name
                ] = machine_backend.state_record

            for resource_backend in plugin.resource_backends():
                self.resource_backend_defns[
                    resource_backend.nix_name
                ] = resource_backend.definition_record
                self.resource_backend_states[
                    resource_backend.database_name
                ] = resource_backend.state_record

    def list_plugins_with_names(self) -> List[str]:
        return sorted(self.pm.list_name_plugin())

    def nix_expressions(self) -> List[Path]:
        return list(self._nix_expressions)

    def get_resource_backend_definition_for(
        self, nix_name: str
    ) -> Optional[Type[ResourceDefinition]]:
        return self.resource_backend_defns.get(nix_name)

    def get_machine_backend_definition_for(
        self, nix_name: str
    ) -> Optional[Type[MachineDefinition]]:
        return self.machine_backend_defns.get(nix_name)

    def get_machine_or_resource_state_for(
        self, database_name: str
    ) -> Union[Type[MachineState], Type[ResourceState], None]:
        return self.get_resource_backend_state_for(
            database_name
        ) or self.get_machine_backend_state_for(database_name)

    def get_resource_backend_state_for(
        self, database_name: str
    ) -> Optional[Type[ResourceState]]:
        return self.resource_backend_states.get(database_name)

    def get_machine_backend_state_for(
        self, database_name: str
    ) -> Optional[Type[MachineState]]:
        return self.machine_backend_states.get(database_name)

    def extend_cli(self, parser: ArgumentParser, subparsers: _SubParsersAction) -> None:
        for plugin in self._plugins:
            plugin.cli_extension(parser, subparsers)


registered_plugins = NixOpsFeatureful()
