from nixops.nix_expr import RawValue, py2nix
import subprocess
import typing
from typing import Optional, Mapping, Any, List, Dict, TextIO
import json
from nixops.util import ImmutableValidatedObject
from nixops.exceptions import NixError
import itertools
import os.path
import os


class NixEvalError(NixError):
    pass


class MalformedNetworkError(NixError):
    pass


class GenericStorageConfig(ImmutableValidatedObject):
    provider: str
    configuration: typing.Mapping[typing.Any, typing.Any]


class GenericLockConfig(ImmutableValidatedObject):
    provider: str
    configuration: typing.Mapping[typing.Any, typing.Any]


class NetworkEval(ImmutableValidatedObject):
    storage: GenericStorageConfig
    lock: GenericLockConfig
    description: str = "Unnamed NixOps network"
    enableRollback: bool = False


class RawNetworkEval(ImmutableValidatedObject):
    storage: Optional[Mapping[str, Any]]
    lock: Optional[Mapping[str, Any]]
    description: Optional[str]
    enableRollback: Optional[bool]


class EvalResult(ImmutableValidatedObject):
    exists: bool
    value: Any


def get_expr_path() -> str:
    expr_path: str = os.path.realpath(
        os.path.dirname(__file__) + "/../../../../share/nix/nixops"
    )
    if not os.path.exists(expr_path):
        expr_path = os.path.realpath(
            os.path.dirname(__file__) + "/../../../../../share/nix/nixops"
        )
    if not os.path.exists(expr_path):
        expr_path = os.path.dirname(__file__) + "/../nix"
    return expr_path


def eval(
    # eval-machine-info args
    networkExprs: List[str],
    uuid: str,
    deploymentName: str,
    args: Dict[str, str],
    pluginNixExprs: List[str],
    checkConfigurationOptions: bool = True,
    # Extend internal defaults
    nix_path: List[str] = [],
    # nix-instantiate args
    attr: Optional[str] = None,
    extra_flags: List[str] = [],
    # Non-propagated args
    stderr: Optional[TextIO] = None,
) -> Any:
    # eval_flags:  = []

    argv: List[str] = (
        ["nix-instantiate", "--eval-only", "--json", "--strict"]
        + [os.path.join(get_expr_path(), "eval-machine-info.nix")]
        + ["-I", "nixops=" + get_expr_path()]
        + [
            "--arg",
            "networkExprs",
            py2nix([RawValue(x) if x[0] == "<" else x for x in networkExprs]),
        ]
        + [
            "--arg",
            "args",
            py2nix({key: RawValue(val) for key, val in args.items()}, inline=True),
        ]
        + ["--argstr", "uuid", uuid]
        + ["--argstr", "deploymentName", deploymentName]
        + ["--arg", "pluginNixExprs", py2nix(pluginNixExprs)]
        + ["--arg", "checkConfigurationOptions", json.dumps(checkConfigurationOptions)]
        + list(itertools.chain(*[["-I", x] for x in (nix_path + pluginNixExprs)]))
        + extra_flags
    )

    if attr:
        argv.extend(["-A", attr])

    try:
        ret = subprocess.check_output(argv, stderr=stderr, text=True)
        return json.loads(ret)
    except OSError as e:
        raise Exception("unable to run ‘nix-instantiate’: {0}".format(e))
    except subprocess.CalledProcessError:
        raise NixEvalError


def _eval_attr(attr, nix_expr: str) -> EvalResult:
    p = subprocess.run(
        [
            "nix-instantiate",
            "--eval-only",
            "--json",
            "--strict",
            # Arg
            "--arg",
            "checkConfigurationOptions",
            "false",
            # Attr
            "--argstr",
            "attr",
            attr,
            "--arg",
            "nix_expr",
            nix_expr,
            "--expr",
            """
              { nix_expr, attr }:
              let
                ret = let
                  v = (import nix_expr);
                in if builtins.typeOf v == "lambda" then v {} else v;
              in {
                exists = ret ? "${attr}";
                value = ret."${attr}" or null;
              }
            """,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode())

    return EvalResult(**json.loads(p.stdout))


def eval_network(nix_expr: str) -> NetworkEval:
    result = _eval_attr("network", nix_expr)

    if not result.exists:
        raise MalformedNetworkError(
            """
TODO: improve this error to be less specific about conversion, and less
about storage backends, and more about the construction of a network
attribute value. link to docs about storage drivers and lock drivers.


WARNING: NixOps 1.0 -> 2.0 conversion step required

NixOps 2.0 added support for multiple storage backends.

Upgrade steps:
1. Open %s
2. Add:
    network.storage.legacy = {
      databasefile = "~/.nixops/deployments.nixops"
    }
3. Rerun
"""
            % nix_expr
        )

    if not isinstance(result.value, dict):
        raise MalformedNetworkError(
            """
TODO: improve this error to be less specific about conversion, and less
about storage backends, and more about the construction of a network
attribute value. link to docs about storage drivers and lock drivers.

The network.nix has a `network` attribute set, but it is of the wrong
type. A valid network attribute looks like this:

  {
    network = {
      storage = {
        /* storage driver details */
      };
    };
  }
"""
        )

    raw_eval = RawNetworkEval(**result.value)

    storage: Mapping[str, Any] = raw_eval.storage or {}
    if len(storage) > 1:
        raise MalformedNetworkError(
            "Invalid property: network.storage can only have one defined storage backend."
        )
    storage_config: Optional[Mapping[str, Any]]
    try:
        storage_key = list(storage.keys()).pop()
        storage_value = storage[storage_key]
        storage_config = {"provider": storage_key, "configuration": storage_value}
    except IndexError:
        raise MalformedNetworkError(
            "Missing property: network.storage has no defined storage backend."
        )

    lock: Mapping[str, Any] = raw_eval.lock or {}
    if len(lock) > 1:
        raise MalformedNetworkError(
            "Invalid property: network.lock can only have one defined lock backend."
        )

    lock_config: Optional[Mapping[str, Any]]
    try:
        lock_key = list(lock.keys()).pop()
        lock_config = {
            "provider": lock_key,
            "configuration": lock[lock_key],
        }
    except IndexError:
        lock_config = {
            "provider": "noop",
            "configuration": {},
        }

    return NetworkEval(
        enableRollback=raw_eval.enableRollback or False,
        description=raw_eval.description or "Unnamed NixOps network",
        storage=storage_config,
        lock=lock_config,
    )
