# -*- coding: utf-8 -*-

# Arbitrary JSON.

import os
import nixops.util
import nixops.resources
from nixops.operation_options import CreateOptions, DestroyOptions

import tempfile
import subprocess
import hashlib


# For typing
from nixops.nix_expr import Function
from nixops.resources import ResourceOptions
from typing import Optional, Dict, Tuple


class CommandOutputOptions(ResourceOptions):
    script: str
    name: str


class CommandOutputDefinition(nixops.resources.ResourceDefinition):
    """Definition of a Command Output."""

    config: CommandOutputOptions

    @classmethod
    def get_type(cls):
        # type: () -> (str)
        return "command-output"

    @classmethod
    def get_resource_type(cls):
        # type: () -> (str)
        return "commandOutput"

    def show_type(self):
        # type: () -> (str)
        return "{0}".format(self.get_type())


class CommandOutputState(nixops.resources.ResourceState[CommandOutputDefinition]):
    """State of a Command Output."""

    state = nixops.util.attr_property(
        "state", nixops.resources.ResourceState.MISSING, int
    )
    script = nixops.util.attr_property("script", None)
    value = nixops.util.attr_property("value", None)
    commandName = nixops.util.attr_property("name", None)

    @classmethod
    def get_type(cls):
        # type: () -> (str)
        return "command-output"

    @property
    def resource_id(self):
        # type: () -> Optional[str]
        if self.value is not None:
            # Avoid printing any potential secret information
            return "{0}-{1}".format(
                self.commandName, hashlib.sha256(self.value.encode()).hexdigest()[:32]
            )
        else:
            return None

    def create(
        self,
        options: CreateOptions[CommandOutputDefinition]
    ) -> None:
        defn = options.definition
        if (
            (defn.config.script is not None)
            and (self.script != defn.config.script)
            or self.value is None
        ):
            self.commandName = defn.name
            try:
                output_dir = nixops.util.SelfDeletingDir(
                    tempfile.mkdtemp(prefix="nixops-output-tmp")
                )

                self.log("Running shell function for output ‘{0}’...".format(defn.name))
                env = {}  # type: Dict[str,str]
                env.update(os.environ)
                env.update({"out": output_dir})
                res = subprocess.check_output(
                    [defn.config.script], env=env, shell=True, text=True
                )
                with self.depl._db:
                    self.value = res
                    self.state = self.UP
                    self.script = defn.config.script
            except Exception:
                self.log("Creation failed for output ‘{0}’...".format(defn.name))
                raise

    def prefix_definition(self, attr):
        # type: (Dict[str,Function]) -> Dict[Tuple[str,str],Dict[str,Function]]
        return {("resources", "commandOutput"): attr}

    def get_physical_spec(self):
        # type: () -> Dict[str,str]
        return {"value": self.value}

    def destroy(self, options: DestroyOptions[CommandOutputDefinition]) -> bool:
        if self.depl.logger.confirm(
            "are you sure you want to destroy {0}?".format(self.name)
        ):
            self.log("destroying...")
        else:
            raise Exception("can't proceed further")
            return False
        self.value = None
        self.state = self.MISSING
        return True
