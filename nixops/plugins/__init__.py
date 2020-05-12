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

        self._nix_expressions: Set[Path] = set()

        for plugin in self.pm.hook.register_plugin():
            # todo: verify that all the nix names and database names are unique across machine and resource backends

            self._nix_expressions.update(plugin.nix_expression_files())

    def list_plugins_with_names(self) -> List[str]:
        return sorted(self.pm.list_name_plugin())

    def nix_expressions(self) -> List[Path]:
        return list(self._nix_expressions)

    def extend_cli(self, parser: ArgumentParser, subparsers: _SubParsersAction) -> None:
        self.pm.hook.parser(parser=parser, subparsers=subparsers)


registered_plugins = NixOpsFeatureful()
