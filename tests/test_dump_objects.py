# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from auto_intersphinx.cli import main


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_help(capsys, option):
    try:
        main(["dump-objects"] + [option])
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "Dumps objects documented in a Sphinx inventory URL" in output


def test_python_3_dump(capsys):
    try:
        main(["dump-objects", "-vvv", "https://docs.python.org/3/objects.inv"])
    except SystemExit:
        pass

    output = capsys.readouterr().out
    assert "" in output
    assert "Dumping https://docs.python.org/3/objects.inv" in output
    assert "library/os" in output
