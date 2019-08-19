#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from configparser import ConfigParser, NoSectionError
from pathlib import Path
from unittest import mock
from unittest.mock import call

import pytest
from rigel import utils
from rigel.pipeline.enums import ClassificationResult
from rigel.pipeline.sk_pipeline import SKLearnPipeline, PipelineException


@pytest.fixture()
def test_instance(tmpdir):
    data_loader = mock.Mock()
    data_loader.path = Path(tmpdir)
    return SKLearnPipeline(ConfigParser(), data_loader)


class TestSKLearnPipeline:

    @staticmethod
    def test_save(test_instance):
        single = mock.Mock()
        dual = mock.Mock()
        multi = mock.Mock()

        test_instance.single_label_problem = single
        test_instance.multi_label_problem = multi
        test_instance.dual_problem = dual
        test_instance._save_problems = mock.Mock()
        utils.get_module_version = mock.Mock()
        utils.get_module_version.return_value = "1.0.0"
        test_instance.save()
        assert test_instance.config_parser.get('rigel', 'version') == "1.0.0"
        assert test_instance.config_parser.get('rigel', 'pipeline') == "sklearn"
        test_instance._save_problems.assert_called_with([single, multi, dual])

    @staticmethod
    def test_save_raise_if_incomplete_pipeline(test_instance):
        with pytest.raises(PipelineException) as e:
            test_instance.save()
        assert "incomplete pipeline" in e.value.message

        test_instance.single_label_problem = mock.Mock()
        with pytest.raises(PipelineException) as e:
            test_instance.save()
        assert "incomplete pipeline" in e.value.message

    @staticmethod
    def test_build_problem_raise_if_unknown_problem_type(test_instance):
        with pytest.raises(NoSectionError):
            test_instance._build_problem("unknown type")

    @staticmethod
    def test_predict(test_instance):
        test_instance.single_label_problem = mock.Mock()
        test_instance.single_label_problem.predict.return_value = ["MIT"]
        test_instance.dual_problem = mock.Mock()
        test_instance.dual_problem.predict.return_value = [ClassificationResult.SINGLE.value]
        test_instance.multi_label_problem = mock.Mock()
        test_instance.multi_label_problem.predict.return_value = ["some", "multi", "license"]

        assert test_instance.predict("This is some text") == ["MIT"]
        test_instance.dual_problem.predict.return_value = [ClassificationResult.MULTI.value]
        assert test_instance.predict("Some other text") == ["some", "multi", "license"]
        test_instance.multi_label_problem.predict.return_value = []
        assert test_instance.predict("bla bla") == [ClassificationResult.UNCLASSIFIED.value]
