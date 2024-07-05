# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
import subprocess
import sys
import typing

# this import avoids a pytest warning
import auto_intersphinx  # noqa: F401


def _sphinx_build_html(
    dir: pathlib.Path,
    rst: typing.Iterable[str],
    conf: typing.Iterable[str],
) -> tuple[int, str, str, pathlib.Path, pathlib.Path]:
    """Runs ``sphinx-build -b html`` over input data and return results.

    This function will create a temporary directory containing the test
    documents composed of a single RST file and a Sphinx configuration file. It
    will then call the command-line program ``sphinx-build``, to build the
    documentation.  It returns the program exit status, the stdout, stderr
    streams, and a path leading to the root of the document tree.

    Arguments:

        dir: Path to a (temporary) directory to be used to create the ``doc``
            and resulting ``html`` directories for this build.  You must manage
            the creation and eventual destruction of this directory.  This
            function will **NOT** do it.

        rst: Strings corresponding to the RST file to use for testing.  Each
            entry in the iterable corresponds to a new line in test RST file.

        A string corresponding to the contents of the single file that
            will be created on the documentation tree.

        conf: Strings corresponding to the configuration to test.  The
            configuration has a Python syntax, each string corresponds to one
            new line to be added to the configuration file.


    Returns:

        A tuple, that contains the exit code of running ``sphinx-build``, its
        stdout and stderr outputs, and finally the paths leading to the
        source "doc" and resulting "html" build directories.
    """

    # prepares the "doc" directory
    srcdir = dir / "doc"
    os.makedirs(srcdir, exist_ok=False)
    with open(srcdir / "index.rst", "w") as f:
        f.write("\n".join(rst))

    pre_conf = [
        "master_doc='index'",
        "source_suffix='.rst'",
        "extensions=['auto_intersphinx']",
    ]

    with open(srcdir / "conf.py", "w") as f:
        f.write("\n".join(pre_conf + list(conf)))

    # runs sphinx
    htmldir = dir / "html"
    proc = subprocess.run(
        f"sphinx-build -aE -b html {srcdir} {htmldir}".split(),
        capture_output=True,
        text=True,
    )

    return proc.returncode, proc.stdout, proc.stderr, srcdir, htmldir


def test_basic_functionality(tmp_path) -> None:
    python_version = "%d.%d" % sys.version_info[:2]
    conf = [
        f"auto_intersphinx_packages=[('python', '{python_version}'), 'numpy']",
    ]

    index_rst = [
        "* Python: :class:`list`, :func:`os.path.basename`",
        "* Numpy: :class:`numpy.ndarray`",
    ]

    status, stdout, stderr, _, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert (
        f"loading intersphinx inventory from "
        f"https://docs.python.org/{sys.version_info[0]}.{sys.version_info[1]}" in stdout
    )

    assert (
        "loading intersphinx inventory from https://numpy.org/doc/stable/objects.inv"
        in stdout
    )

    assert (htmldir / "index.html").exists()

    assert len(stderr) == 0


def test_warnings_dev_and_base(tmp_path) -> None:
    conf = [
        "auto_intersphinx_packages=[('numpy', 'latest'), 'numpy']",
    ]

    index_rst = [
        "* Python: :class:`list`, :func:`os.path.basename`",
        "* Numpy: :class:`numpy.ndarray`",
    ]

    status, stdout, stderr, _, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert (
        "loading intersphinx inventory from https://numpy.org/devdocs/objects.inv"
        in stdout
    )

    assert "Ignoring reset of `numpy' intersphinx_mapping" in stderr

    assert (htmldir / "index.html").exists()


def test_can_remove_duplicates_without_warning(tmp_path) -> None:
    conf = [
        "auto_intersphinx_packages=['numpy', 'numpy']",
    ]

    index_rst = [
        "* Python: :class:`list`, :func:`os.path.basename`",
        "* Numpy: :class:`numpy.ndarray`",
    ]

    status, stdout, _, _, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert "loading intersphinx inventory from https://numpy.org/doc/stable/" in stdout

    assert "Ignoring repeated setting of `numpy' intersphinx_mapping" in stdout

    assert (htmldir / "index.html").exists()


def test_conflict_from_intersphinx_mapping(tmp_path) -> None:
    conf = [
        "intersphinx_mapping={'numpy': ('https://numpy.org/doc/stable/', None)}",
        "auto_intersphinx_packages=['numpy']",
    ]

    index_rst = [
        "* Python: :class:`list`, :func:`os.path.basename`",
        "* Numpy: :class:`numpy.ndarray`",
    ]

    status, stdout, _, _, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert "loading intersphinx inventory from https://numpy.org/doc/stable/" in stdout

    assert "Ignoring repeated setting of `numpy' intersphinx_mapping" in stdout

    assert (htmldir / "index.html").exists()


def test_discover_from_internal_catalog(tmp_path) -> None:
    conf = [
        "auto_intersphinx_packages=['setuptools']",
    ]

    index_rst = [
        "* Python: :class:`list`, :func:`os.path.basename`",
        "* Numpy: :class:`numpy.ndarray`",
    ]

    status, stdout, _, _, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert "loading intersphinx inventory from https://setuptools" in stdout

    assert (htmldir / "index.html").exists()


def test_warning_with_internal_catalog(tmp_path) -> None:
    conf = [
        "auto_intersphinx_packages=[('setuptools', '61.0.0')]",
    ]

    index_rst = [
        "* Python: :class:`list`, :func:`os.path.basename`",
        "* Numpy: :class:`numpy.ndarray`",
    ]

    status, stdout, stderr, _, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert "Cannot find suitable catalog entry for `setuptools@61.0.0'" in stderr

    assert (htmldir / "index.html").exists()


def test_error_unknown_package(tmp_path) -> None:
    conf = [
        "auto_intersphinx_packages=[('setuptoolx', '61.0.0'), ('dead-beef-xyz')]",
    ]

    index_rst = [
        "* Python: :class:`list`, :func:`os.path.basename`",
        "* Numpy: :class:`numpy.ndarray`",
    ]

    status, stdout, stderr, _, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert "Cannot find suitable catalog entry for `setuptoolx@61.0.0'" in stderr

    assert "Cannot find suitable catalog entry for `dead-beef-xyz@stable'" in stderr

    assert (htmldir / "index.html").exists()


def test_discover_from_metadata(tmp_path) -> None:
    conf = [
        "auto_intersphinx_packages=['jinja2']",
    ]

    index_rst = [
        "* Python: :class:`list`, :func:`os.path.basename`",
        "* Numpy: :class:`numpy.ndarray`",
    ]

    status, stdout, _, _, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert (
        "loading intersphinx inventory from https://jinja.palletsprojects.com/"
        in stdout
    )

    assert (htmldir / "index.html").exists()


def test_create_user_catalog(tmp_path) -> None:
    conf = [
        "auto_intersphinx_packages=['flask']",
        "auto_intersphinx_catalog='catalog.json'",
    ]

    index_rst = [
        "* Flask: :mod:`flask`",
    ]

    status, stdout, _, srcdir, htmldir = _sphinx_build_html(
        tmp_path,
        index_rst,
        conf,
    )

    assert status == 0

    assert (
        "loading intersphinx inventory from https://flask.palletsprojects.com/"
        in stdout
    )

    assert (srcdir / "catalog.json").exists()

    assert (htmldir / "index.html").exists()
