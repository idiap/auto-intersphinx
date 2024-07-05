# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from auto_intersphinx.catalog import BUILTIN_CATALOG
from auto_intersphinx.cli import main


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_help(capsys, option):
    try:
        main(["update-catalog"] + [option])
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Updates catalog of intersphinx cross-references" in output


def test_dump(capsys, tmp_path):
    output_catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "-vvv",
                f"--output={str(output_catalog)}",
            ]
        )
    except SystemExit:
        pass

    assert output_catalog.exists()
    assert BUILTIN_CATALOG.read_text() == output_catalog.read_text()

    output = capsys.readouterr().out
    assert "click" not in output
    assert "https://pypi.org/pypi/numpy/json" not in output
    assert "https://readthedocs.org/projects/packaging/versions/" not in output


def test_dump2(capsys, datadir, tmp_path):
    input_catalog = datadir / "catalog.json"
    output_catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "-vvv",
                f"--catalog={str(input_catalog)}",
                f"--output={str(output_catalog)}",
            ]
        )
    except SystemExit:
        pass

    assert output_catalog.exists()
    assert input_catalog.read_text() == output_catalog.read_text()

    output = capsys.readouterr().out
    assert "click" not in output
    assert "https://pypi.org/pypi/numpy/json" not in output
    assert "https://readthedocs.org/projects/packaging/versions/" not in output


def test_verbose_0(capsys, datadir, tmp_path):
    input_catalog = datadir / "catalog.json"
    output_catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                f"--catalog={str(input_catalog)}",
                f"--output={str(output_catalog)}",
            ]
        )
    except SystemExit:
        pass

    assert output_catalog.exists()
    assert input_catalog.read_text() == output_catalog.read_text()

    output = capsys.readouterr().out
    assert output == ""


def test_verbose_1(capsys, datadir, tmp_path):
    input_catalog = datadir / "catalog.json"
    output_catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "-v",
                f"--catalog={str(input_catalog)}",
                f"--output={str(output_catalog)}",
            ]
        )
    except SystemExit:
        pass

    assert output_catalog.exists()
    assert input_catalog.read_text() == output_catalog.read_text()

    output = capsys.readouterr().out
    assert output == ""


def test_verbose_2(capsys, datadir, tmp_path):
    input_catalog = datadir / "catalog.json"
    output_catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "-vv",
                f"--catalog={str(input_catalog)}",
                f"--output={str(output_catalog)}",
            ]
        )
    except SystemExit:
        pass

    assert output_catalog.exists()
    assert input_catalog.read_text() == output_catalog.read_text()

    output = capsys.readouterr().out
    assert output == ""


def test_self_update(capsys, datadir, tmp_path):
    input_catalog = datadir / "catalog.json"
    output_catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "-vvv",
                "--self",
                f"--catalog={str(input_catalog)}",
                f"--output={str(output_catalog)}",
            ]
        )
    except SystemExit:
        pass

    assert output_catalog.exists()

    output = capsys.readouterr().out
    assert "click" not in output
    assert "https://pypi.org/pypi/numpy/json" in output
    assert "https://readthedocs.org/projects/packaging/versions/" in output


def test_boostrap_from_package_list(capsys, tmp_path):
    catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "-vvv",
                "--keep-going",
                "--pypi-max-entries=2",
                f"--catalog={str(catalog)}",
                f"--output={str(catalog)}",
                "numpy",
                "requests",
                "click",
            ]
        )
    except SystemExit:
        pass

    assert catalog.exists()

    output = capsys.readouterr().out
    assert "click" in output
    assert "numpy" in output
    assert "requests" in output
    assert "https://readthedocs.org/projects/click/versions/" in output
    assert "https://pypi.org/pypi/click/json" in output
    assert "https://pypi.org/pypi/numpy/json" in output
    assert "https://pypi.org/pypi/requests/json" in output
    assert "Saving package catalog with 3 entries at" in output


def test_boostrap_from_package_list_to_stdout(capsys, tmp_path):
    catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "-vvv",
                "--keep-going",
                "--pypi-max-entries=2",
                f"--catalog={str(catalog)}",
                "numpy",
                "requests",
                "click",
            ]
        )
    except SystemExit:
        pass

    assert not catalog.exists()

    output = capsys.readouterr().out
    assert "click" in output
    assert "numpy" in output
    assert "requests" in output
    assert "https://readthedocs.org/projects/click/versions/" in output
    assert "https://pypi.org/pypi/click/json" in output
    assert "https://pypi.org/pypi/numpy/json" in output
    assert "https://pypi.org/pypi/requests/json" in output
    assert '"readthedocs": "numpy"' in output
    assert '"readthedocs": "click"' in output
    assert '"readthedocs": "requests"' in output


def test_boostrap_from_file(capsys, datadir, tmp_path):
    requirements = datadir / "requirements.txt"
    catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "-vvv",
                "--keep-going",
                "--pypi-max-entries=0",
                f"--catalog={str(catalog)}",
                f"--output={str(catalog)}",
                f"{str(requirements)}",
            ]
        )
    except SystemExit:
        pass

    assert catalog.exists()

    output = capsys.readouterr().out
    assert "click" in output
    assert "numpy" in output
    assert "requests" in output
    assert "https://readthedocs.org/projects/click/versions/" in output
    assert "https://pypi.org/pypi/click/json" in output
    assert "https://pypi.org/pypi/numpy/json" in output
    assert "https://pypi.org/pypi/requests/json" in output
    assert "Saving package catalog with 13 entries at" in output


def test_remote_list_does_not_exist(capsys, tmp_path):
    address = "https://example.com/does/not/exist/requirements.txt"
    catalog = tmp_path / "catalog.json"

    try:
        main(
            [
                "update-catalog",
                "--keep-going",
                "--pypi-max-entries=0",
                f"--catalog={str(catalog)}",
                f"--output={str(catalog)}",
                address,
            ]
        )
    except SystemExit:
        pass

    assert not catalog.exists()

    output = capsys.readouterr().out
    assert f"[ERROR] Could not retrieve `{address}'" == output.strip()
