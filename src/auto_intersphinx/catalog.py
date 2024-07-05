# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause
"""This module contains instructions for documentation lookup."""

from __future__ import annotations  # not required for Python >= 3.10

import collections.abc
import importlib.metadata
import importlib.resources
import json
import pathlib
import re
import shutil
import typing

import lxml.html
import packaging.version
import requests

from sphinx.util import logging

logger = logging.getLogger(__name__)


PackageDictionaryType = dict[str, dict[str, str]]
"""Type for the internal values of :py:class:`Catalog`"""


BUILTIN_CATALOG = importlib.resources.files(__package__).joinpath("catalog.json")
"""Base name for the catalog file distributed with this package."""


PEP440_RE = re.compile(
    r"^\s*" + packaging.version.VERSION_PATTERN + r"\s*$",
    re.VERBOSE | re.IGNORECASE,
)
"""Regular expression for matching PEP-440 version numbers."""


def _ensure_webdir(addr: str) -> str:
    """Ensures the web-address ends in a /, and contains ``objects.inv``"""
    if addr.endswith(".html"):
        addr = addr[: addr.rfind("/")]
    if not addr.endswith("/"):
        addr += "/"

    # objects = addr + "/" + "objects.inv"
    # if requests.head(objects).ok:
    #     logger.error("Cannot find {objects}...")
    #     return None

    return addr


def _reorder_versions(vdict: dict[str, str]) -> dict[str, str]:
    """Re-orders version dictionary by decreasing version."""
    # nota bene: new dicts preserve insertion order
    retval: dict[str, str] = {}

    # these keys come always first, if available
    protected = ("latest", "main", "master", "stable")
    for key in protected:
        if key in vdict:
            retval[key] = vdict[key]

    # next, are releases in reverse order
    version_map = {
        packaging.version.Version(k): k
        for k in vdict.keys()
        if (k not in protected) and PEP440_RE.match(k)
    }
    for version in sorted(version_map.keys(), reverse=True):
        retval[version_map[version]] = vdict[version_map[version]]

    # now, everything else
    retval.update({k: v for k, v in vdict.items() if k not in retval})

    return retval


def docurls_from_environment(package: str) -> dict[str, str]:
    """Checks installed package metadata for documentation URLs.

    Arguments:

        package: Name of the package you want to check

        version: A version such as "stable", "latest" or a formal version
            number parsed by :py:class:`packaging.version.Version`.


    Returns:

        A dictionary, that maps the version of the documentation found on PyPI
        to the URL.
    """
    try:
        md = importlib.metadata.metadata(package)
        if md.get_all("Project-URL") is None:
            return {}
        for k in md.get_all("Project-URL"):
            if k.startswith(("documentation, ", "Documentation, ")):
                addr = _ensure_webdir(k.split(",", 1)[1].strip())
                if requests.head(addr + "/objects.inv").ok:
                    try:
                        return {md["version"]: addr}
                    except KeyError:
                        return {"latest": addr}

    except importlib.metadata.PackageNotFoundError:
        pass

    return {}


def docurls_from_rtd(package: str) -> dict[str, str]:
    """Checks readthedocs.org for documentation pointers for the package.

    Arguments:

        package: Name of the package to check on rtd.org - this must be the
            name it is know at rtd.org and not necessarily the package name.
            Some packages do have different names on rtd.org.


    Returns:

        A dictionary, which contains all versions of documentation available
        for the given package on RTD.  If the package's documentation is not
        available on RTD, returns an empty dictionary.
    """
    try:
        url = f"https://readthedocs.org/projects/{package}/versions/"
        logger.debug(f"Reaching for `{url}'...")
        r = requests.get(f"https://readthedocs.org/projects/{package}/versions/")
        if r.ok:
            tree = lxml.html.fromstring(r.text)
            return {
                k.text: _ensure_webdir(k.attrib["href"])
                for k in tree.xpath("//a[contains(@class, 'module-item-title')]")
                if k.attrib["href"].startswith("http")
            }

    except requests.exceptions.RequestException:
        pass

    return {}


def _get_json(url: str) -> dict | None:
    try:
        logger.debug(f"Reaching for `{url}'...")
        r = requests.get(url)
        if r.ok:
            return r.json()

    except requests.exceptions.RequestException:
        pass

    return None


def docurls_from_pypi(package: str, max_entries: int) -> dict[str, str]:
    """Checks PyPI for documentation pointers for a given package.

    This procedure first looks up the main repo JSON entry, and then figures
    out all available versions of the package.  In a second step, and depending
    on the value of ``max_entries``, this function will retrieve the latest
    ``max_entries`` available on that particular package.


    Arguments:

        package: Name of the PyPI package you want to check

        max_entries: The maximum number of entries to lookup in PyPI.  A value
            of zero will download only the main package information and will
            hit PyPI only once.  A value bigger than zero will download at most
            the information from the last ``max_entries`` releases.  Finally, a
            negative value will imply the download of all available releases.


    Returns:

        A dictionary, that maps the version of the documentation found on PyPI
        to the URL.
    """
    versions: dict[str, str] = {}
    data = _get_json(f"https://pypi.org/pypi/{package}/json")
    if data is None:
        return versions

    urls = data["info"]["project_urls"]
    addr = urls.get("Documentation") or urls.get("documentation")
    if addr is not None:
        addr = _ensure_webdir(addr)
        if requests.head(addr + "/objects.inv").ok:
            versions[data["info"]["version"]] = addr

    # download further versions, if requested by user
    version_map = {
        packaging.version.Version(k): k
        for k in data["releases"].keys()
        if PEP440_RE.match(k)
    }
    versions_to_probe = sorted(list(version_map.keys()), reverse=True)

    if max_entries >= 0:
        versions_to_probe = versions_to_probe[:max_entries]

    for k in versions_to_probe:
        data = _get_json(f"https://pypi.org/pypi/{package}/{version_map[k]}/json")
        if data is None:
            continue

        urls = data["info"]["project_urls"]
        addr = urls.get("Documentation") or urls.get("documentation")
        if addr is not None:
            addr = _ensure_webdir(addr)
            if requests.head(addr + "/objects.inv").ok:
                versions[data["info"]["version"]] = addr

    return versions


class Catalog(collections.abc.MutableMapping):
    """A type that can lookup and store information about Sphinx documents.

    The object is organised as a dictionary (mutable mapping type) with extra
    methods to handle information update from various sources. Information is
    organised as dictionary mapping Python package names to another dictionary
    containing the following entries:

    * ``versions``: A dictionary mapping version numbers to URLs.  The keys
      have free form, albeit are mostly PEP440 version numbers.  Keywords such
      as ``stable``, ``latest``, ``master``, or ``main`` are typically found as
      well.
    * ``sources``: A dictionary mapping information sources for this particular
      entry.  Keys are one of ``pypi``, ``readthedocs`` or ``environment``.
      Values correspond to specific names used for the lookup of the
      information on those sources.


    Attributes:

        _data: Internal dictionary containing the mapping between package names
            the user can refer to, versions and eventual sources of such
            information.
    """

    _data: dict[str, PackageDictionaryType]

    def __init__(self) -> None:
        self.reset()

    def load(self, path: pathlib.Path) -> None:
        """Loads and replaces contents with those from the file."""
        with path.open("rt") as f:
            logger.debug(f"Loading package catalog from {str(path)}...")
            self._data = json.load(f)
            logger.debug(f"Loaded {len(self)} entries from {str(path)}")

    def loads(self, contents: str) -> None:
        """Loads and replaces contents with those from the string."""
        self._data = json.loads(contents)
        logger.debug(f"Loaded {len(self)} entries from string")

    def dump(self, path: pathlib.Path) -> None:
        """Loads and replaces contents with those from the file."""
        if path.exists():
            backup = path.with_suffix(path.suffix + "~")
            logger.debug(f"Backing up: {str(path)} -> {str(backup)}...")
            shutil.copy(path, backup)  # backup

        with path.open("wt") as f:
            logger.debug(
                f"Saving package catalog with {len(self)} entries at {str(path)}..."
            )
            json.dump(self._data, f, indent=2)
            f.write("\n")  # avoids pre-commit/self-update conflicting changes

    def dumps(self) -> str:
        """Loads and replaces contents with those from the string."""
        return json.dumps(self._data, indent=2)

    def reset(self) -> None:
        """Full resets internal catalog."""
        self._data = {}

    # mutable mapping operations, so this looks like a dictionary
    def __getitem__(self, key: str) -> PackageDictionaryType:
        return self._data[key]

    def __setitem__(self, key: str, value: PackageDictionaryType) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._data)

    def __repr__(self) -> str:
        return repr(self._data)

    def _ensure_defaults(self, pkg: str) -> None:
        """Ensures a standardised setup for a package entry."""
        self.setdefault(pkg, {"versions": {}, "sources": {}})
        self[pkg].setdefault("versions", {})
        self[pkg].setdefault("sources", {})

    def update_versions_from_environment(self, pkg: str, name: str | None) -> bool:
        """Replaces package documentation URLs using information from current
        Python environment.

        Arguments:

            pkg: Name of the package as one would find in pypi.org. This
              name can be different then that of the Python package
              itself.

            name: This is the name of the package as installed on the current
                environment. Sometimes, this name can be different then that of
                the Python package itself. If this value is set to ``None``,
                then we just use ``pkg`` as the name to lookup.


        Returns:

            ``True``, if the update was successful (found versions), or
            ``False``, otherwise.
        """

        self._ensure_defaults(pkg)

        name = name or pkg

        logger.debug(f"{pkg}: checking current Python environment for {name}...")

        versions = docurls_from_environment(name)
        logger.debug(
            f"{pkg}: Found {len(versions)} doc URL(s) at current Python environment"
        )

        if versions:
            self[pkg]["versions"].update(versions)
            self[pkg]["versions"] = _reorder_versions(self[pkg]["versions"])
            self[pkg]["sources"]["environment"] = name

        return len(versions) > 0

    def update_versions_from_rtd(self, pkg: str, name: str | None) -> bool:
        """Replaces package documentation URLs using information from
        readthedocs.org.

        Arguments:

            pkg: Name of the Python package to update versions for.

            name: This is the name of the package on readthedocs.org. Often,
                this name is different then that of the Python package itself.
                If this value is set to ``None``, then we just use ``pkg`` as
                the name to lookup.


        Returns:

            The dictionary of values for the current package, as obtained from
            readthedocs.org, and potentially merged with the existing one.
        """
        self._ensure_defaults(pkg)

        name = name or pkg

        logger.debug(f"{pkg}: checking readthedocs.org for {name}...")

        versions = docurls_from_rtd(name)
        logger.debug(f"{pkg}: Found {len(versions)} doc URL(s) at readthedocs.org")

        if versions:
            self[pkg]["versions"].update(versions)
            self[pkg]["versions"] = _reorder_versions(self[pkg]["versions"])
            self[pkg]["sources"]["readthedocs"] = name

        return len(versions) > 0

    def update_versions_from_pypi(
        self, pkg: str, name: str | None, max_entries: int
    ) -> bool:
        """Replaces package documentation URLs using information from pypi.org.

        Arguments:

            pkg: Name of the package as one would find in pypi.org. This
              name can be different then that of the Python package
              itself.

            name: This is the name of the package on pypi.org. Sometimes, this
                name can be different then that of the Python package itself.
                If this value is set to ``None``, then we just use ``pkg`` as
                the name to lookup.

            max_entries: The maximum number of entries to lookup in PyPI.  A
                value of zero will download only the main package information
                and will hit PyPI only once.  A value bigger than zero will
                download at most the information from the last ``max_entries``
                releases.  Finally, a negative value will imply the download of
                all available releases.


        Returns:

            The dictionary of values for the current package, as obtained from
            pypi.org, and potentially merged with the existing one.
        """

        self._ensure_defaults(pkg)

        name = name or pkg

        logger.debug(f"{pkg}: checking pypi.org for {name}...")

        versions = docurls_from_pypi(name, max_entries)
        logger.debug(f"{pkg}: Found {len(versions)} doc URL(s) at pypi.org")

        if versions:
            self[pkg]["versions"].update(versions)
            self[pkg]["versions"] = _reorder_versions(self[pkg]["versions"])
            self[pkg]["sources"]["pypi"] = name

        return len(versions) > 0

    def update_versions(
        self,
        pkgs: typing.Iterable[str],
        order: typing.Iterable[str] = ["environment", "readthedocs", "pypi"],
        names: dict[str, dict[str, str]] = {},
        pypi_max_entries: int = 0,
        keep_going: bool = False,
    ) -> None:
        """Updates versions for a list of packages in this catalog.

        This method will add a list of packages defined by ``pkgs`` (list of
        names) into its own catalog.  The order of look-ups by default is set
        by the ``order``, and it is the following:

        1. Current Python environment (``environment``)
        2. readthedocs.org (``readthedocs``)
        3. PyPI (``pypi``)


        Arguments:

            pkgs: List of packages that will have their versions updated

            order: A list, containing the order in which lookup will happen.
                There are only 3 possible keys that can be used here:
                ``environment``, which stands for finding package metadata from
                the currently installed Python environment, ``readthedocs``,
                which will trigger readthedocs.org lookups, and ``pypi``, which
                will trigger pypi.org lookups from uploaded packages.

            names: A dictionary, that eventually maps source names (as in
                ``order``) to another dictionary that maps package names to to
                their supposed names on readthedocs.org, pypi.org or the current
                environment.  If keys for various packages are not available, then
                their package names are used.  If the keys exist, but are set
                to ``None``, then lookup for that particular source is skipped.

            pypi_max_entries: The maximum number of entries to lookup in PyPI.
                A value of zero will download only the main package information
                and will hit PyPI only once.  A value bigger than zero will
                download at most the information from the last ``max_entries``
                releases.  Finally, a negative value will imply the download of
                all available releases.

            keep_going: By default, the method stops adding a package when a
                hit is found (in either of these sources of information).  If
                the flag ``keep_going`` is set to ``True`` (defaults to
                ``False``), then it merges information from all sources.  Note
                that some of this information may be repetitive.
        """

        for pkg in pkgs:
            for action in order:
                if action == "environment":
                    name = names.get(action, {}).get(pkg, pkg)
                    if name is not None:
                        ok = self.update_versions_from_environment(pkg, name)
                        if ok and not keep_going:
                            break

                elif action == "readthedocs":
                    name = names.get(action, {}).get(pkg, pkg)
                    if name is not None:
                        ok = self.update_versions_from_rtd(pkg, name)
                        if ok and not keep_going:
                            break

                elif action == "pypi":
                    name = names.get(action, {}).get(pkg, pkg)
                    if name is not None:
                        ok = self.update_versions_from_pypi(pkg, name, pypi_max_entries)
                        if ok and not keep_going:
                            break

                else:
                    raise RuntimeError(f"Unrecognized source: {action}")

    def self_update(self) -> None:
        """Runs a self-update procedure, by re-looking up known sources."""
        # organises the names as expected by update_versions()
        names: dict[str, dict[str, str]] = dict(environment={}, readthedocs={}, pypi={})
        for pkg, info in self.items():
            for src in ("environment", "readthedocs", "pypi"):
                names[src][pkg] = info["sources"].get(src)

        self.update_versions(pkgs=self.keys(), names=names)


def _string2version(v: str) -> packaging.version.Version | None:
    """Converts a string into a version number.

    This method covers various specific use-cases:

    * ``1.2.3`` -> specific version
    * ``1.2.x``, ``1.2`` -> anything in the ``[1.2.0, 1.3.0)`` range
    * ``1.x.x``, ``1`` -> anything in the ``[1.0.0, 2.0.0)`` range
    * anything else: discarded

    Arguments:

        v: a string containing the version number to be parsed, like the ones
           in the catalog


    Returns:

        Either ``None``, or the version object with the parsed version.
    """
    v = v.replace(".x", "")
    try:
        return packaging.version.Version(v)
    except packaging.version.InvalidVersion:
        return None


def _prepare_versions(versions: dict[str, str]) -> dict[str, str]:
    """Prepares a dictionary of versions for structured lookups.

    This procedure:

    1. Ensures there is one ``latest`` and ``stable`` entries in the input
       dictionary
    2. Augment the version dictionary with PEP-440 version numbers (e.g.
       annotates ``v2.2.0`` -> ``2.2.0``, or ``1.x`` -> ``1``)


    Arguments:

        versions: A dictionary that maps release version (and aliases such as
        ``stable`` or ``latest`` to URLs that contain Sphinx-generated
        documentation.


    Returns:

        A dictionary with keys that correspond to parsed versions and aliases.
    """
    if not versions:
        return versions

    # see what each valid number means
    version_map = {_string2version(k): k for k in versions.keys()}
    sorted_versions = sorted([k for k in version_map.keys() if k is not None])

    retval: dict[str, str] = {}
    if sorted_versions:
        # there is at least 1 (valid) version number
        latest = sorted_versions[-1]
        retval["latest"] = versions.get("latest", versions[version_map[latest]])

        stable_versions = [
            k for k in sorted_versions if not (k.is_prerelease or k.is_devrelease)
        ]
        if stable_versions:
            stable = stable_versions[-1]
        else:
            stable = latest
        retval["stable"] = versions.get("stable", versions[version_map[stable]])

        # fill-in the remainder of the versions, leave latest on top
        for k in reversed(sorted_versions):
            retval[version_map[k]] = versions[version_map[k]]
            if ".x" in version_map[k]:
                # copy to a shortened version number as well
                retval[version_map[k].replace(".x", "")] = versions[version_map[k]]
            elif k.public != version_map[k]:
                # copy a standardised version number as well
                retval[k.public] = versions[version_map[k]]

    else:
        # there is either nothing, or just aliases such as stable/latest
        retval["latest"] = (
            versions.get("latest")
            or versions.get("stable")
            or versions.get("master")
            or versions.get("main")
            or ""
        )
        retval["stable"] = (
            versions.get("stable")
            or versions.get("latest")
            or versions.get("master")
            or versions.get("main")
            or ""
        )

    return retval


class LookupCatalog:
    """A catalog that guarantees standardised version lookups.

    Arguments:

        catalog: The catalog to use as base for the lookup.
    """

    def __init__(self, catalog: Catalog):
        self._catalog = catalog
        self.reset()

    def reset(self):
        """Internally creates all possible aliases for package names and
        versions.

        This method will expand the catalog package names and version
        numbers so that the user can refer to these using environment,
        readthedocs.org or pypi.org names for packages, and PEP-440
        compatible strings for version names during the lookup.

        The catalog associated to this lookup is not modified in this
        process. All augmentations are built-into the object instance.
        """
        self._version_map: dict[str, dict[str, str]] = {}
        self._package_map: dict[str, str] = {}
        for pkg in self._catalog.keys():
            self._version_map[pkg] = _prepare_versions(self._catalog[pkg]["versions"])

            # translations from Python, rtd.org or pypi.org names
            self._package_map[pkg] = pkg
            self._package_map.update(
                {v: pkg for v in self._catalog[pkg]["sources"].values()}
            )

    def get(self, pkg: str, version: str | None, default: typing.Any = None):
        """Accesses one single ``pkg/version`` documentation URL.

        Arguments:

            pkg: The package name, as available on the catalog or through one
              of its environment, readthedocs.org or pypi.org names.

            version: The version of the package to search for.  This must be
              either an identifier from readthedocs.org or pypi.org, or a valid
              PEP-440 version number as a string.

            default: The default value to return in case we do not find a
            match.


        Returns:

            If a match is found, returns the URL for the documentation.
            Otherwise, returns the ``default`` value.
        """
        if pkg not in self._package_map:
            return default
        if version not in self._version_map[pkg]:
            return default
        return self._version_map[self._package_map[pkg]][version]
