from __future__ import annotations
from typing import Mapping, Dict, Any, Type, TYPE_CHECKING
from typing_extensions import Protocol, TypedDict

if TYPE_CHECKING:
    import nixops.statefile


StorageArgValues = Mapping[str, Any]


class StorageBackend(Protocol):
    def __init__(self, args: StorageArgValues) -> None:
        raise NotImplementedError

    # fetchToFile: acquire a lock and download the state file to
    # the local disk. Note: no arguments will be passed over kwargs.
    # Making it part of the type definition allows adding new
    # arguments later.
    def fetchToFile(self, path: str, **kwargs) -> None:
        raise NotImplementedError

    # onOpen: receive the StateFile object for last-minute, backend
    # specific changes to the state file.
    # Note: no arguments will be passed over kwargs. Making it part
    # of the type definition allows adding new arguments later.
    def onOpen(self, sf: nixops.statefile.StateFile, **kwargs) -> None:
        pass

    # uploadFromFile: upload the new state file and release any locks
    # Note: no arguments will be passed over kwargs. Making it part of
    # the type definition allows adding new arguments later.
    def uploadFromFile(self, path: str, **kwargs) -> None:
        raise NotImplementedError


BackendRegistration = Dict[str, Type[StorageBackend]]


storage_backends: Dict[str, Type[StorageBackend]] = {}
