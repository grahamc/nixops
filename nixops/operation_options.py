from typing import Generic, Optional
from .resources import ResourceDefinitionType

class CreateOptions(Generic[ResourceDefinitionType]):
    definition: ResourceDefinitionType
    check: bool
    allow_reboot: bool
    allow_recreate: bool

    def __init__(self, definition: ResourceDefinitionType, check: bool, allow_reboot: bool, allow_recreate: bool) -> None:
        self.definition = definition
        self.check = check
        self.allow_reboot = allow_reboot
        self.allow_recreate = allow_recreate

class DestroyOptions(Generic[ResourceDefinitionType]):
    wipe: bool

    def __init__(self, wipe: bool) -> None:
        self.wipe = wipe
