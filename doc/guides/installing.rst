Installing with Plugins
=======================

NixOps with plugins provides seamless support for provisioning
servers and other cloud resources from a variety of providers. In this
guide, we will create a distribution of NixOps equipped with the
`nixops-aws <https://github.com/NixOS/nixops-aws>`_ plugin.

Prerequisites
-------------

You will need:

* Nix
* A computer capable of building x86_64-linux Nix builds, like an
  x86_64 laptop running Linux or a macOS laptop with an x86_64 remote
  builder configured.

This guide will be working inside a Git repository to track our work.

Getting Started
---------------

NixOps is a standard Python application, and its plugins are standard
Python modules. This guide will use standard Python packaging to
create a NixOps with the specific plugins we want.

Here, we will use Poetry.

Step One: Creating a Poetry Environment
***************************************

Create a ``shell.nix``:

.. code-block:: nix

  { pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    name = "example-nixops-build";
    buildInputs = [ pkgs.poetry ];
  }

then enter this Nix shell environment with ``nix-shell``::

  example-nixops-build$ nix-shell
  [nix-shell]$


and run ``poetry init`` to create a basic ``pyproject.toml`` file.
This file will record our list of plugins and dependencies::

  [nix-shell]$ poetry init

  This command will guide you through creating your pyproject.toml config.

  Package name [example-nixops-build]:
  Version [0.1.0]:
  Description []:  My project's custom NixOps build with plugins.
  Author [Graham Christensen <graham@grahamc.com>, n to skip]:
  License []:  MIT
  Compatible Python versions [^3.7]:

  Would you like to define your main dependencies interactively? (yes/no) [yes] no
  Would you like to define your development dependencies interactively? (yes/no) [yes] no
  Generated file

  [tool.poetry]
  name = "example-nixops-build"
  version = "0.1.0"
  description = "My project's custom NixOps build with plugins."
  authors = ["Graham Christensen <graham@grahamc.com>"]
  license = "MIT"

  [tool.poetry.dependencies]
  python = "^3.7"

  [tool.poetry.dev-dependencies]

  [build-system]
  requires = ["poetry>=0.12"]
  build-backend = "poetry.masonry.api"


  Do you confirm generation? (yes/no) [yes] yes

Now add both the ``shell.nix`` and ``pyproject.toml`` files to source
control and commit::

  [nix-shell]$ git add shell.nix pyproject.toml
  [nix-shell]$ git commit -m "Record our shell.nix and pyproject.toml for tracking NixOps plugin dependencies"


Step Two: Add NixOps as a Dependency
************************************

Add NixOps as a dependency. We will use NixOps's master branch today.
Once NixOps 2.0 is released, it will be better to use a specific
version tag instead.

From within our Nix shell from Step One, use Poetry to add NixOps as
a dependency::

  [nix-shell]$ poetry add git+https://github.com/NixOS/nixops.git
  Creating virtualenv example-nixops-build-DaSIGgdg-py3.7 in /home/grahamc/.cache/pypoetry/virtualenvs

  Updating dependencies
  Resolving dependencies... (1.3s)


  Package operations: 6 installs, 0 updates, 0 removals

    - Installing zipp (3.1.0)
    - Installing importlib-metadata (1.6.0)
    - Installing pluggy (0.13.1)
    - Installing prettytable (0.7.2)
    - Installing typeguard (2.7.1)
    - Installing nixops (x.x.x xxxxxxx)

Looking at ``git diff``, we should see NixOps is now a dependency::

  [nix-shel]$ git diff
  diff --git a/pyproject.toml b/pyproject.toml
  index 8ec328e..0bb25de 100644
  --- a/pyproject.toml
  +++ b/pyproject.toml
  @@ -7,6 +7,7 @@ license = "MIT"

   [tool.poetry.dependencies]
   python = "^3.7"
  +nixops = {git = "https://github.com/NixOS/nixops.git"}

   [tool.poetry.dev-dependencies]

Poetry has also created a lock file containing all of the precise
dependency versions we require. Let's commit both of those now::

  [nix-shell]$ git add pyproject.toml poetry.lock

  [nix-shell]$ git status
  On branch master
  Changes to be committed:
	new file:   poetry.lock
	modified:   pyproject.toml

  [nix-shell]$ git commit -m "pyproject: add NixOps"
  [master 89b2e64] pyproject: add NixOps
   2 files changed, 110 insertions(+)
   create mode 100644 poetry.lock

Step Three: Add ``nixops-aws`` as a Dependency
**********************************************

This is just like Step Three, but with the
`nixops-aws <https://github.com/NixOS/nixops-aws>`_ project. Just like
with NixOps, once NixOps 2.0 is released, it will be better to depend
on a specific tagged version of nixops-aws instead of the master
branch.

Inside our Nix shell, use Poetry to add nixops-aws as a dependency::

  [nix-shell]$ poetry add git+https://github.com/NixOS/nixops-aws.git
  Creating virtualenv example-nixops-build-DaSIGgdg-py3.7 in /home/grahamc/.cache/pypoetry/virtualenvs
