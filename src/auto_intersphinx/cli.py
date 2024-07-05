# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations  # not required for Python >= 3.10

import argparse
import sys


def make_parser() -> argparse.ArgumentParser:
    """Creates the main parser."""
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description="Commands to handle sphinx catalogs.",
    )
    subparsers = parser.add_subparsers(help="commands")

    from . import check_packages

    check_packages.add_parser(subparsers)

    from . import dump_objects

    dump_objects.add_parser(subparsers)

    from . import update_catalog

    update_catalog.add_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> None:
    # parse and execute
    parser = make_parser()
    args = parser.parse_args(argv)
    args.func(args)
