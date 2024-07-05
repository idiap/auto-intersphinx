.. SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
..
.. SPDX-License-Identifier: BSD-3-Clause

.. _auto_intersphinx.usage:

=======
 Usage
=======

To use this extension, first enable it on your ``conf.py`` file for Sphinx_:

.. code-block:: python

   extensions += ["auto_intersphinx"]


You do not need to both enable this extension and ``sphinx.ext.intersphinx``
because this extension will load that automatically.

Once you have enabled the extension, create a single variable with the names of
the packages you want to cross-reference:

.. code-block:: python

   auto_intersphinx_packages = ["sphinx", "requests", "packaging"]


Optionally, add a catalog file path (relative to ``conf.py``) that will be used
to cache any lookups we may have to do during Sphinx_ document building.

.. code-block:: python

   auto_intersphinx_catalog = "catalog.json"


How does it work?
-----------------

Auto-intersphinx works by automatically populating ``intersphinx_mapping``
dictionary using URLs that are stored in the built-in JSON catalog of URLs or
your own.  If URLs for a package are not found on these catalogs,
auto-intersphinx checks the installed Python packages and then tries to go
online searching for those cross-references.  Here is the rough algorithm,
performed for each entry in the ``auto_intersphinx_packages`` list:

1. If an intersphinx_ URL for the given package on the user catalog, that is
   used prioritarily, and the ``intersphinx_mapping`` for that package is
   filled and the algorithm continues with the next package.
2. Else, we check the built-in catalog, distributed with auto-intersphinx.  If
   an URL for the package is found there, then we fill-in
   ``intersphinx_mapping`` and continue.
3. Else, we check the current Python environment, searching for the package
   metadata and attached documentation URLs the project may declare.  Many
   projects declare their Sphinx_ documents this way.  If an URL is found, it
   is checked for an ``objects.inv`` file existing there (not downloaded at
   this point), and if that exists, it added to the user catalog, allowing it
   to be added to the ``intersphinx_mapping``.  If successful, the algorithm
   then goes to the next package.
4. If you get to this point, then auto-intersphinx will look for the package's
   "versions" page in https://readthedocs.org.  If one is found, then we
   download the information on that page, which includes documentation pointers
   and store these in the user catalog.  We do not check for ``objects.inv``
   file at those URLs since readthedocs_ documents are all Sphinx_-compatible.
   If successful, the algorithm adds the ``intersphinx_mapping`` entry for the
   package, and then goes to the next package.
5. Finally, if nothing else worked, we will look at the project metadata for
   the package at https://pypi.org.  PyPI_ metadata often contains
   documentation URL for packages.  If that is the case, we test it for the
   presence of an ``objects.inv`` file and, if successful, add that information
   to the user catalog. If successful, the algorithm populates the
   ``intersphinx_mapping``, and goes to the next package.

   At this point, if we still do not find the relevant documentation for the
   package, auto-intersphinx will generate a build error which will cause
   Sphinx_ to exit with an error condition at the end of the processing.

By the end of the processing, if the user catalog was changed with respect to
the state registered on the disk, and a filename has been defined by setting
``auto_intersphinx_catalog``, it is saved back to that file (a backup is
created if needed), so that the next lookup will not require probing remote
resources.  You may commit this JSON file to your repository and keep it there.


The Catalog
-----------

The lookup algorithm above may be optimised/improved/fixed in several ways.  To
avoid unnecessary lookups, it is recommended to setup your own catalog of
entries to covering all your documentation needs.  Setting up
``auto_intersphinx_catalog`` may help you kick-starting this work.

Moreover, often, names of packages as they are known in Python, at readthedocs_
or PyPI_, may differ from the package name you typically use while importing
such package.  This may lead the lookup algorithm to search for incorrect
entries in these environments.  Here is a list of issues one can typically find
while trying to create a coherent set of ``intersphinx_mapping`` entries:

    * **Package names may be different than what you use for importing them
      into your code**.  For example, you may import ``docker`` in your code,
      however the readthedocs_ entry for this package lives under the name
      docker-py_. The PyPI version of the package is placed under docker_.  The
      famous machine learning package pytorch_ is distributed as torch_ inside
      PyPI_.

    * **Packages may not explicitly define their documentation URLs, or be
      available on readthedocs_**.  For example, pytorch_ has a broken set of
      links on readthedocs_, and self-hosts their own documentation.

    * **Packges may not be available while you build your documentation**, and
      therefore may not be looked-up at the current environment.

The URL catalog format has been designed to accomodate these exceptions and
skip automated (online) searches if possible.  It is a JSON file that contains
a dictionary, mapping names you'd use as inputs in
``auto_intersphinx_packages`` to another dictionary composed of two keys:
``versions`` and ``sources``. Here is an example:

.. code-block:: json

   {
     "click": {
       "versions": {
         "latest": "https://click.palletsprojects.com/en/latest/",
         "8.1.x": "https://click.palletsprojects.com/en/8.1.x/",
         "8.0.x": "https://click.palletsprojects.com/en/8.0.x/",
       },
       "sources": {}
     },
     "docker": {
       "versions": {
         "latest": "https://docker-py.readthedocs.io/en/latest/",
         "stable": "https://docker-py.readthedocs.io/en/stable/",
         "5.0.3": "https://docker-py.readthedocs.io/en/5.0.3/",
         "5.0.2": "https://docker-py.readthedocs.io/en/5.0.2/",
         "5.0.1": "https://docker-py.readthedocs.io/en/5.0.1/",
         "5.0.0": "https://docker-py.readthedocs.io/en/5.0.0/",
       },
       "sources": {
         "readthedocs": "docker-py"
       }
     },
     "numpy": {
       "versions": {
         "latest": "https://numpy.org/devdocs/",
         "stable": "https://numpy.org/doc/stable/",
         "1.23.x": "https://numpy.org/doc/1.23/",
         "1.22.x": "https://numpy.org/doc/1.22/",
         "1.21.x": "https://numpy.org/doc/1.21/"
       },
       "sources": {
         "pypi": "numpy"
       }
     }
   }

The ``versions`` entry of each package determine version name to URL mappings.
When you do not explicitly request a particular version number catalog to be
linked for a package, the ``stable`` (or ``latest``) versions are used.  The
``sources`` entry indicate where information for this package can be found.
Examples are ``environment``, ``readthedocs`` or ``pypi``.  The values
correspond to the name that should ber looked up on those services for finding
information about that package.

In the example above, the package ``click`` has 3 versions encoded in the
catalog, the user can ask for.  Furthermore, no online services have
information about this package (probably the user hard-coded those URLs after
inspection).  The various versions of the package docker documentation may be
obtained on readthedocs_ under the name ``docker-py``.  Finally, ``numpy``
information may be obtained at PyPI_, under the name ``numpy``.


Bootstrapping a Catalog
=======================

A new user catalog is typically saved on the directory containing the file
``conf.py``, if the user specified the Sphinx_ configuration parameter
``auto_intersphinx_catalog`` with a relative path name (e.g. ``catalog.json``).
However, the user may create and maintain their own catalog file using
command-line utilities shiped with this package.

To bootstrap a new catalog from scratch, specifying the list of packages to
lookup and populate it with, and use the program
:ref:`auto_intersphinx.cli.update_catalog`:

.. code-block:: sh

   auto-intersphinx-update-catalog -vvv --catalog=catalog.json numpy requests click

This will create a new file called ``catalog.json`` on your directory, and will
try to apply the lookup algorithm explained above to find sources of
documentation for these packages.  You may hand-edit or improve this catalog
later.

.. tip::

   You may bootstrap a new catalog from either a list of packages, as above, or
   by providing the path (or URL) of a pip-requirements style file.  The
   command-line application ``auto-intersphinx-update-catalog`` will parse such
   a file, search for resources, and fill-in a catalog.


.. tip::

   Read the application documentation with ``auto-intersphinx-update-catalog
   --help`` for usage instructions.


Updating a Catalog
==================

To update an existing catalog, use the command-line application
:ref:`auto_intersphinx.cli.update_catalog`:

.. code-block:: sh

   auto-intersphinx update-catalog -vvv --self --catalog=catalog.json

This will read the current information available in the existing catalog, and
will search the sources once more for updated information.  Naturally, packages
with no sources (empty ``sources``) entries, will **not** be updated.


Browsing for Documentation
--------------------------

You may ask the command-line application
:ref:`auto_intersphinx.cli.check_packages` to display where documentation
information may be found for a package.  For example:

.. code-block:: sh

   $ auto-intersphinx check-packages numpy
   Found numpy in builtin catalog:
   | {
   |   "latest": "https://numpy.org/devdocs/",
   |   "stable": "https://numpy.org/doc/stable/",
   |   "1.23.4": "https://numpy.org/doc/1.23/",
   |   "1.23.x": "https://numpy.org/doc/1.23/",
   |   "1.22.x": "https://numpy.org/doc/1.22/",
   |   "1.21.x": "https://numpy.org/doc/1.21/",
   |   "1.20.x": "https://numpy.org/doc/1.20/"
   | }

You may ask this tool to keep going and find all sources of information for a
package:

.. code-block:: sh

   $ auto-intersphinx-check-packages numpy --keep-going
   Found numpy in builtin catalog:
   | {
   |   "latest": "https://numpy.org/devdocs/",
   |   "stable": "https://numpy.org/doc/stable/",
   |   "1.23.4": "https://numpy.org/doc/1.23/",
   |   "1.23.x": "https://numpy.org/doc/1.23/",
   |   "1.22.x": "https://numpy.org/doc/1.22/",
   |   "1.21.x": "https://numpy.org/doc/1.21/",
   |   "1.20.x": "https://numpy.org/doc/1.20/"
   | }
   Found numpy documentation in readthedocs.org:
   | {
   |   "latest": "https://numpy.readthedocs.io/en/latest/",
   |   "main": "https://numpy.readthedocs.io/en/main/"
   | }
   Looking up all PyPI versions of numpy - this may be long...
   Found numpy documentation in PyPI:
   | {
   |   "1.23.4": "https://numpy.org/doc/1.23/"
   | }

Which may display more information about the package's various sources.  The
flag ``--keep-going`` may also be used at ``auto-intersphinx-update-catalog``
to complete information about a package.  While here the ``versions``
dictionary are displayed in sections, while updating the catalogs, the
resulting ``versions`` dictionaries are merged together.  Of course, you still
have the option to copy-and-paste information from the above output, directly
to your catalog.


Inspecting intersphinx Inventories
----------------------------------

It is sometimes useful to inspect the contents of ``objects.inv`` files
available locally or remotely.  To this end, we provide a CLI application
called :ref:`auto_intersphinx.cli.dump_objects`, that can be used to dump the
contents of both local or remote inventories.  Read the application
documentation with ``--help``, to discover usage examples.


.. include:: links.rst
