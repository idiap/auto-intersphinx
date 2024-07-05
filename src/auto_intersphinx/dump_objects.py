# Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import argparse
import textwrap

from sphinx.util import logging

from .update_catalog import setup_verbosity

logger = logging.getLogger(__name__)


def _main(args) -> None:
    """Main function, that actually executes the dump-objects command."""
    setup_verbosity(args.verbose)

    from sphinx.ext import intersphinx

    for k in args.url:
        logger.info(f"Dumping {k}...")
        intersphinx.inspect_main([k])


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Just sets up the parser for this CLI."""
    prog = "auto-intersphinx dump-objects"

    parser = subparsers.add_parser(
        prog.split()[1],
        help="Dumps objects documented in a Sphinx inventory URL",
        description="Dumps objects documented in a Sphinx inventory URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            f"""
            examples:

            1. Dumps objects documented in a local Sphinx build:

               .. code:: sh

                  {prog} html/objects.inv


            2. Dumps objects documented in python 3.x:

               .. code:: sh

                  {prog} https://docs.python.org/3/objects.inv


            3. Dumps objects documented in numpy:

               .. code:: sh

                  {prog} https://docs.scipy.org/doc/numpy/objects.inv
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
        "url",
        nargs="*",
        default=[],
        help="``objects.inv`` URL to parse and dump (can refer to a local file)",
    )

    parser.set_defaults(func=_main)

    return parser
