# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations  # not required for Python >= 3.10

import argparse
import importlib.resources
import json
import pathlib
import textwrap

from . import oneliner
from .catalog import (
    Catalog,
    docurls_from_environment,
    docurls_from_pypi,
    docurls_from_rtd,
)
from .update_catalog import setup_verbosity


def _main(args) -> None:
    """Main function, that actually executes the check-package command."""
    setup_verbosity(args.verbose)

    builtin_catalog = Catalog()
    if not args.no_builtin:
        catalog_file = importlib.resources.files(__name__.split(".", 1)[0]).joinpath(
            "catalog.json"
        )
        builtin_catalog.loads(catalog_file.read_text())

    user_catalog = Catalog()
    if args.user:
        user_catalog.load(args.user)

    for p in args.packages:
        if p in user_catalog:
            print(f"Found {p} in user catalog:")
            print(
                textwrap.indent(
                    json.dumps(user_catalog[p]["versions"], indent=2), "  | "
                )
            )
            if not args.keep_going:
                continue

        if p in builtin_catalog:
            print(f"Found {p} in builtin catalog:")
            print(
                textwrap.indent(
                    json.dumps(builtin_catalog[p]["versions"], indent=2), "  | "
                )
            )
            if not args.keep_going:
                continue

        if not args.no_environment:
            versions = docurls_from_environment(p)
            if versions:
                print(f"Found {p} documentation in installed Python environment:")
                print(textwrap.indent(json.dumps(versions, indent=2), "  | "))
                if not args.keep_going:
                    continue

        if not args.no_rtd:
            versions = docurls_from_rtd(p)
            if versions:
                print(f"Found {p} documentation in readthedocs.org:")
                print(textwrap.indent(json.dumps(versions, indent=2), "  | "))
                if not args.keep_going:
                    continue

        if not args.no_pypi:
            print(f"Looking up all PyPI versions of {p} - this may be long...")
            versions = docurls_from_pypi(p, args.pypi_max_entries)
            if versions:
                print(f"Found {p} documentation in PyPI:")
                print(textwrap.indent(json.dumps(versions, indent=2), "  | "))
                if not args.keep_going:
                    continue


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Just sets up the parser for this CLI."""
    prog = "auto-intersphinx check-packages"

    parser = subparsers.add_parser(
        prog.split()[1],
        help="Discover documentation cross-references for packages",
        description="Discover documentation cross-references for packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            f"""
            examples:

            1. Checks internal catalog, Python environment, readthedocs.org and
               PyPI for package "requests":

               .. code:: sh

                  {prog} requests

            2. Checks internal and user catalog, Python environment,
               readthedocs.org and PyPI for package "requests":

               .. code:: sh

                  {prog} --user=doc/catalog.json requests

            3. Skip internal catalog checks when running for package "requests"
               (checks readthedocs.org and PyPI only):

               .. code:: sh

                  {prog} --no-builtin requests

            4. Keep looking for references in all available places (do not stop
               when first finds a documentation link, such as the extension does):

               .. code:: sh

                  {prog} --keep-going requests
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
        "packages",
        nargs="+",
        help="Names of packages to check - specify one or more",
    )

    parser.add_argument(
        "-S",
        "--no-builtin",
        action="store_true",
        default=False,
        help="If set, then do not check own catalog",
    )

    parser.add_argument(
        "-E",
        "--no-environment",
        action="store_true",
        default=False,
        help="If set, then do not check the current environment package documentation",
    )

    parser.add_argument(
        "-R",
        "--no-rtd",
        action="store_true",
        default=False,
        help="If set, then do not check readthedocs.org for package documentation",
    )

    parser.add_argument(
        "-P",
        "--no-pypi",
        action="store_true",
        default=False,
        help="If set, then do not check PyPI for package documentation",
    )

    parser.add_argument(
        "-M",
        "--pypi-max-entries",
        default=0,
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
        "-u",
        "--user",
        type=pathlib.Path,
        help="If set, then also checks the local user-catalog at the specified path",
    )

    parser.set_defaults(func=_main)

    return parser
