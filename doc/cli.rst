.. SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
..
.. SPDX-License-Identifier: BSD-3-Clause

========================
 Command-line Interface
========================

This section includes information for using scripts shipped with
``auto-intersphinx``.


auto-intersphinx
----------------

.. argparse::
   :module: auto_intersphinx.cli
   :func: make_parser
   :prog: auto-intersphinx
   :nosubcommands:
   :nodescription:

   Commands to handle sphinx catalogs.

   Sub-commands:

   * :ref:`auto_intersphinx.cli.check_packages`: Discover documentation cross-references for packages
   * :ref:`auto_intersphinx.cli.dump_objects`: Dumps all the objects given an (inter) Sphinx inventory URL
   * :ref:`auto_intersphinx.cli.update_catalog`: Discover documentation cross-references for packages


.. _auto_intersphinx.cli.check_packages:

check-packages
--------------

.. argparse::
   :module: auto_intersphinx.cli
   :func: make_parser
   :prog: auto-intersphinx
   :path: check-packages


.. _auto_intersphinx.cli.dump_objects:

dump-objects
------------

.. argparse::
   :module: auto_intersphinx.cli
   :func: make_parser
   :prog: auto-intersphinx
   :path: dump-objects


.. _auto_intersphinx.cli.update_catalog:

update-catalog
--------------

.. argparse::
   :module: auto_intersphinx.cli
   :func: make_parser
   :prog: auto-intersphinx
   :path: update-catalog


.. include:: links.rst
