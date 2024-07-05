# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations  # not required for Python >= 3.10

import argparse
import importlib.abc
import os
import pathlib
import re
import sys
import textwrap

import requests

from sphinx.util import logging

from . import oneliner
from .catalog import BUILTIN_CATALOG, Catalog

logger = logging.getLogger(__name__)


def _parse_requirements(contents: str) -> list[str]:
    """Parses a pip-requirements file and extracts package lists."""
    lines = contents.split()
    lines = [k.strip() for k in lines if not k.strip().startswith("#")]
    split_re = re.compile(r"[=\s]+")
    return [split_re.split(k)[0] for k in lines]


def setup_verbosity(verbose: int) -> None:
    """Sets up logger verbosity."""
    import logging as builtin_logging

    package_logger = builtin_logging.getLogger("sphinx." + __package__)

    handler = builtin_logging.StreamHandler(sys.stdout)
    formatter = builtin_logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(builtin_logging.DEBUG)

    package_logger.addHandler(handler)
    if verbose == 0:
        package_logger.setLevel(builtin_logging.ERROR)
    elif verbose == 1:
        package_logger.setLevel(builtin_logging.WARNING)
    elif verbose == 2:
        package_logger.setLevel(builtin_logging.INFO)
    else:
        package_logger.setLevel(builtin_logging.DEBUG)


def _main(args) -> None:
    """Main function, that actually executes the update-catalog command."""
    setup_verbosity(args.verbose)

    catalog = Catalog()

    if isinstance(args.catalog, str):
        catalog_path = pathlib.Path(args.catalog)
        if catalog_path.exists():
            catalog.load(catalog_path)
        else:
            logger.info(
                f"Input catalog file `{str(args.catalog)}' does not "
                f"exist. Skipping..."
            )
    elif isinstance(args.catalog, importlib.abc.Traversable):
        catalog.loads(args.catalog.read_text())

    if args.self:
        catalog.self_update()

    package_list = []
    for pkg in args.packages:
        if pkg.startswith("http"):
            logger.info(f"Retrieving package list from `{pkg}'...")
            r = requests.get(pkg)
            if r.ok:
                package_list += _parse_requirements(r.text)
            else:
                logger.error(f"Could not retrieve `{pkg}'")
                sys.exit(1)

        elif os.path.exists(pkg):
            with open(pkg) as f:
                package_list += _parse_requirements(f.read())

        else:
            package_list.append(pkg)

    if package_list:
        catalog.update_versions(
            pkgs=package_list,
            pypi_max_entries=args.pypi_max_entries,
            keep_going=args.keep_going,
        )

    if args.output:
        catalog.dump(args.output)

    if (args.self or package_list) and args.output is None:
        # an update was run, dump results
        print(catalog.dumps())


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Just sets up the parser for this CLI."""
    prog = "auto-intersphinx update-catalog"

    parser = subparsers.add_parser(
        prog.split()[1],
        help="Updates catalog of intersphinx cross-references",
        description="Updates catalog of intersphinx cross-references",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            f"""
            examples:

            1. Updates numpy and scipy from the internal catalog, dumps new
               catalog to stdout

               .. code:: sh

                  {prog} numpy scipy

            2. Self-update internal catalog:

               .. code:: sh

                  {prog} --self

            3. Refresh internal catalog from a remote pip-constraints.txt file:

               .. code:: sh

                  {prog} https://gitlab.idiap.ch/software/idiap-citools/-/raw/main/src/citools/data/pip-constraints.txt

            4. Run local tests without modifying the package catalog:

               .. code:: sh

                  {prog} --output=testout.json
            """
        ),
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Can be set multiple times to increase console verbosity",
    )

    parser.add_argument(
        "--self",
        action="store_true",
        default=False,
        help="If set, then self-updates catalog entries",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="If set, then dump the existing catalog to an output file",
    )

    parser.add_argument(
        "-c",
        "--catalog",
        default=BUILTIN_CATALOG,
        help="Location of the catalog to update [default: %(default)s]",
    )

    parser.add_argument(
        "-M",
        "--pypi-max-entries",
        default=0,
        type=int,
        help=oneliner(
            """
            The maximum number of entries to lookup in PyPI.  A value of zero
            will download only the main package information and will hit PyPI
            only once.  A value bigger than zero will download at most the
            information from the last ``max_entries`` releases. Finally, a
            negative value will imply the download of all available releases.
            """
        ),
    )

    parser.add_argument(
        "-k",
        "--keep-going",
        action="store_true",
        default=False,
        help=oneliner(
            """
            If set, then do not stop at first found reference (such as
            auto-intersphinx would do), but rather keep searching for all
            references.
            """
        ),
    )

    parser.add_argument(
        "packages",
        nargs="*",
        default=[],
        help=oneliner(
            """
            Location of the reference package list to load to populate catalog.
            If not specified, then does not update anything (unless --self is
            set, of course).  This argument may take multiple inputs. Each
            input may be a filename, which contains package lists, a remote
            http/https file, or a package name.
            """
        ),
    )

    parser.set_defaults(func=_main)

    return parser
