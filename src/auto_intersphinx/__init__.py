# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause
"""Sphinx extension to automatically link package documentation from their
names.

This package contains a Sphinx plugin that can fill intersphinx mappings
based on package names.  It simplifies the use of that plugin by
removing the need of knowing URLs for various API catologs you may want
to cross-reference.
"""

from __future__ import annotations  # not required for Python >= 3.10

import importlib.metadata
import inspect
import pathlib
import textwrap
import typing

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging

from .catalog import BUILTIN_CATALOG, Catalog, LookupCatalog

logger = logging.getLogger(__name__)


def oneliner(s: str) -> str:
    """Transforms a multiline docstring into a single line of text.

    This method converts the multi-line string into a single line, while also
    dedenting the text.


    Arguments:

        s: The input multiline string


    Returns:

        A single line with all text.
    """
    return inspect.cleandoc(s).replace("\n", " ")


def rewrap(s: str) -> str:
    """Re-wrap a multiline docstring into a 80-character format.

    This method first converts the multi-line string into a single line.  It
    then wraps the single line into 80-characters width.


    Arguments:

        s: The input multiline string


    Returns:

        An 80-column wrapped multiline string
    """
    return "\n".join(textwrap.wrap(oneliner(s), width=80))


def _add_index(
    mapping: dict[str, tuple[str, str | None]],
    name: str,
    addr: str,
    objects_inv: str | None = None,
) -> None:
    """Helper to add a new doc index to the intersphinx mapping catalog.

    This function will also verify if repeated entries are being inserted, and
    if will issue a warning or error in case it must ignore overrides.


    Arguments:

        mapping: A pointer to the currently used ``intersphinx_mapping``
            variable
        name: Name of the new package to add
        addr: The URL that contains the ``object.inv`` file, to load for
            mapping objects from that package
        objects_inv: The name of the file to use with the catalog to load on
            the remote address (if different than ``objects.inv``.)
    """

    if name not in mapping:
        mapping[name] = (addr, objects_inv)

    elif mapping[name][0] == addr and mapping[name][1] == objects_inv:
        logger.info(f"Ignoring repeated setting of `{name}' intersphinx_mapping")

    else:
        curr = mapping[name][0]
        curr += "/" if not curr.endswith("/") else ""
        curr += mapping[name][1] if mapping[name][1] else "objects.inv"

        newval = addr
        newval += "/" if not newval.endswith("/") else ""
        newval += objects_inv if objects_inv else "objects.inv"

        logger.error(
            rewrap(
                f"""
                Ignoring reset of `{name}' intersphinx_mapping, because it
                currently already points to `{curr}', and that is different
                from the new value `{newval}'
                """
            )
        )


def populate_intersphinx_mapping(app: Sphinx, config: Config) -> None:
    """Main extension method.

    This function is called by Sphinx once it is :py:func:`setup`.  It executes
    the lookup procedure for all packages listed on the configuration parameter
    ``auto_intersphinx_packages``.  If a catalog name is provided at
    ``auto_intersphinx_catalog``, and package information is not found on the
    catalogs, but discovered elsewhere (environment, readthedocs.org, or
    pypi.org), then it is saved on that file, so that the next lookup is
    faster.

    It follows the following search protocol for each package (first match
    found stops the search procedure):

    1. User catalog (if available)
    2. Built-in catalog distributed with the package
    3. The current Python environment
    4. https://readthedocs.org
    5. https://pypi.org


    Arguments:

        app: Sphinx application

        config: Sphinx configuration
    """
    m = config.intersphinx_mapping

    builtin_catalog = Catalog()
    builtin_catalog.loads(BUILTIN_CATALOG.read_text())
    builtin_lookup = LookupCatalog(builtin_catalog)

    user_catalog = Catalog()

    if config.auto_intersphinx_catalog:
        user_catalog_file = pathlib.Path(config.auto_intersphinx_catalog)
        if not user_catalog_file.is_absolute():
            user_catalog_file = (
                pathlib.Path(app.confdir) / config.auto_intersphinx_catalog
            )
        if user_catalog_file.exists():
            user_catalog.loads(user_catalog_file.read_text())
    user_lookup = LookupCatalog(user_catalog)

    for k in config.auto_intersphinx_packages:
        p, v = k if isinstance(k, (tuple, list)) else (k, "stable")

        addr = user_lookup.get(p, v)
        if addr is not None:
            _add_index(m, p, addr, None)
            continue  # got an URL, continue to next package
        elif p in user_catalog:
            # The user receiving the message has access to their own catalog.
            # Warn because it may trigger a voluntary update action.
            logger.warning(
                rewrap(
                    f"""
                    Package {p} is available in user catalog, however version
                    {v} is not.  You may want to fix or update the catalog?
                    """
                )
            )

        addr = builtin_lookup.get(p, v)
        if addr is not None:
            _add_index(m, p, addr, None)
            continue  # got an URL, continue to next package
        elif p in builtin_catalog:
            # The user receiving the message may not have access to the
            # built-in catalog.  Downgrade message importance to INFO
            logger.info(
                rewrap(
                    f"""
                    Package {p} is available in builtin catalog, however
                    version {v} is not.  You may want to fix or update that
                    catalog?
                    """
                )
            )

        # try to see if the package is installed using the user catalog
        user_catalog.update_versions_from_environment(p, None)
        user_lookup.reset()
        addr = user_lookup.get(p, v)
        if addr is not None:
            _add_index(m, p, addr, None)
            continue  # got an URL, continue to next package
        else:
            logger.info(
                rewrap(
                    f"""
                    Package {p} is not available at your currently installed
                    environment. If the name of the installed package differs
                    from that you specified, you may tweak your catalog using
                    ['{p}']['sources']['environment'] = <NAME> so that the
                    package can be properly found.
                    """
                )
            )

        # try to see if the package is available on readthedocs.org
        user_catalog.update_versions_from_rtd(p, None)
        user_lookup.reset()
        addr = user_lookup.get(p, v)
        if addr is not None:
            _add_index(m, p, addr, None)
            continue  # got an URL, continue to next package
        else:
            logger.info(
                rewrap(
                    f"""
                    Package {p} is not available at readthedocs.org. If the
                    name of the installed package differs from that you
                    specify, you may patch your catalog using
                    ['{p}']['sources']['environment'] = <NAME> so that the
                    package can be properly found.
                    """
                )
            )

        # try to see if the package is available on readthedocs.org
        user_catalog.update_versions_from_pypi(p, None, max_entries=0)
        user_lookup.reset()
        addr = user_lookup.get(p, v)
        if addr is not None:
            _add_index(m, p, addr, None)
            continue  # got an URL, continue to next package
        else:
            logger.info(
                rewrap(
                    f"""
                    Package {p} is not available at your currently installed
                    environment. If the name of the installed package differs
                    from that you specify, you may patch your catalog using
                    ['{p}']['sources']['environment'] = <NAME> so that the
                    package can be properly found.
                    """
                )
            )

        # if you get to this point, then the package name was not
        # resolved - emit an error and continue
        if v is not None:
            name = f"{p}@{v}"
        else:
            name = p

        logger.error(
            rewrap(
                f"""
                Cannot find suitable catalog entry for `{name}'.  I searched
                both internally and online without access.  To remedy this,
                provide the links on your own catalog, be less selective with
                the version to bind documentation to, or simply remove this
                entry from the auto-intersphinx package list.  May be this
                package has no Sphinx documentation at all?
                """
            )
        )

    # by the end of the processing, save the user catalog file if a path was
    # given, so that the user does not have to do this again on the next
    # rebuild, making it work like a cache.
    if config.auto_intersphinx_catalog and user_catalog:
        user_catalog_file = pathlib.Path(config.auto_intersphinx_catalog)
        if not user_catalog_file.is_absolute():
            user_catalog_file = (
                pathlib.Path(app.confdir) / config.auto_intersphinx_catalog
            )
        current_contents: str = ""
        if user_catalog_file.exists():
            current_contents = user_catalog_file.read_text()
        if current_contents != user_catalog.dumps():
            logger.info(
                f"Recording {len(user_catalog)} entries to {str(user_catalog_file)}..."
            )
            user_catalog.dump(user_catalog_file)


def setup(app: Sphinx) -> dict[str, typing.Any]:
    """Sphinx extension configuration entry-point.

    This function defines the main function to be executed, other
    extensions to be loaded, the loading relative order of this
    extension, and configuration options with their own defaults.
    """
    # we need intersphinx
    app.setup_extension("sphinx.ext.intersphinx")

    # List of packages to link, in the format: str | tuple[str, str|None]
    # that indicate either the package name, or a tuple with (package,
    # version), for pointing to a specific version number user guide.
    app.add_config_value("auto_intersphinx_packages", [], "html")

    # Where the user catalog file will be placed, if any.  If a value is set,
    # then it is updated if we discover resources remotely.  It works like a
    # local cache, you can edit to complement the internal catalog.  A relative
    # path is taken w.r.t. the sphinx documentation configuration.
    app.add_config_value("auto_intersphinx_catalog", None, "html")

    app.connect("config-inited", populate_intersphinx_mapping, priority=700)

    return {
        "version": importlib.metadata.version(__package__),
        "parallel_read_safe": True,
    }
