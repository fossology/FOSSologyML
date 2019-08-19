#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2018, Siemens AG
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# SPDX-License-Identifier: GPL-2.0-only

from unittest.mock import patch
import os
import pytest
import rigel.cli.cli
from click.testing import CliRunner
from pkg_resources import get_distribution
from pathlib import Path

from rigel.utils import get_rigel_dir
from rigel.pipeline.enums import ClassificationResult

@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture()
def empty_file(tmpdir):
    test_file = tmpdir.join('test_file.txt')
    test_file.write('')
    return test_file


def test_print_version_succeeds(runner):
    result = runner.invoke(rigel.cli.cli.main, ['--version'])

    assert result.exit_code == 0
    assert get_distribution('rigel').version in result.output


def test_print_help_succeeds(runner):
    result = runner.invoke(rigel.cli.cli.main, ['--help'])

    expected_text = rigel.cli.cli.main.__doc__.split('\n')[0]
    result_text = result.output.split('\n')[1]

    assert result.exit_code == 0
    assert expected_text == result_text


def test_missing_input_path_returns_error(runner):
    result = runner.invoke(rigel.cli.cli.main, [])

    expected = 'Error: Missing argument'

    assert result.exit_code != 0
    assert result.exception
    assert expected in result.output


def test_main_returns_error_on_unhandled_exception(runner, empty_file):
    expected_exception_arg = 'My Dummy Test Exception'

    with patch('rigel.cli.prediction_logic.PredictionLogic.__init__', side_effect=Exception(expected_exception_arg)):
        result = runner.invoke(rigel.cli.cli.main, [empty_file.strpath])

        assert result.exit_code != 0
        assert result.exception
