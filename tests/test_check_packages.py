# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from auto_intersphinx.cli import main


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_help(capsys, option):
    try:
        main(["check-packages"] + [option])
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Discover documentation cross-references for packages" in output


def test_keep_going(capsys):
    try:
        main(["check-packages", "-vvv", "--keep-going", "requests"])
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Found requests in builtin catalog" in output
    assert "Found requests documentation in installed Python environment" in output
    assert "Found requests documentation in readthedocs.org" in output
    assert "Found requests documentation in PyPI" in output


def test_user_catalog(capsys, datadir):
    user_catalog = datadir / "catalog.json"

    try:
        main(
            [
                "check-packages",
                "-vvv",
                f"--user={str(user_catalog)}",
                "--keep-going",
                "click",
            ]
        )
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Found click in user catalog" in output
    assert "Found click in builtin catalog" in output
    assert "Found click documentation in readthedocs.org" in output
    assert "Found click documentation in PyPI" in output


def test_stop_at_user_catalog(capsys, datadir):
    user_catalog = datadir / "catalog.json"

    try:
        main(["check-packages", "-vvv", f"--user={str(user_catalog)}", "click"])
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Found click in user catalog" in output
    assert "Found click in builtin catalog" not in output
    assert "Found click documentation in installed Python environment" not in output
    assert "Found click documentation in readthedocs.org" not in output
    assert "Found click documentation in PyPI" not in output


def test_stop_at_builtin_catalog(capsys):
    try:
        main(["check-packages", "-vvv", "requests"])
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Found requests in user catalog" not in output
    assert "Found requests in builtin catalog" in output
    assert "Found requests documentation in installed Python environment" not in output
    assert "Found requests documentation in readthedocs.org" not in output
    assert "Found requests documentation in PyPI" not in output


def test_stop_at_environment(capsys):
    try:
        main(["check-packages", "-vvv", "--no-builtin", "requests"])
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Found requests in user catalog" not in output
    assert "Found requests in builtin catalog" not in output
    assert "Found requests documentation in installed Python environment" in output
    assert "Found requests documentation in readthedocs.org" not in output
    assert "Found requests documentation in PyPI" not in output


def test_stop_at_readthedocs(capsys):
    try:
        main(
            [
                "check-packages",
                "-vvv",
                "--no-builtin",
                "--no-environment",
                "requests",
            ]
        )
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Found requests in user catalog" not in output
    assert "Found requests in builtin catalog" not in output
    assert "Found requests documentation in installed Python environment" not in output
    assert "Found requests documentation in readthedocs.org" in output
    assert "Found requests documentation in PyPI" not in output


def test_stop_at_pypi(capsys):
    try:
        main(
            [
                "check-packages",
                "-vvv",
                "--no-builtin",
                "--no-environment",
                "--no-rtd",
                "requests",
            ]
        )
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Found requests in user catalog" not in output
    assert "Found requests in builtin catalog" not in output
    assert "Found requests documentation in installed Python environment" not in output
    assert "Found requests documentation in readthedocs.org" not in output
    assert "Found requests documentation in PyPI" in output
