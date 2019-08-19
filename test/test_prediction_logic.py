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

from pathlib import Path
from unittest.mock import patch, Mock, call
import pytest
from rigel.cli.prediction_logic import LocalPredictor, ServerPredictor, PredictionLogicException


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.content = "this is a sample content"
        self.url = "url"
        self.reason = "reason"
        self.text = "text"

    def json(self):
        return self.json_data


def mock_post(endpoint, **json):
    return FakeResponse({"licenses": ["MIT"]})


def test_predict_local():
    pipeline = Mock()
    attrs = {'predict.return_value': ["MIT"], 'save.return_value': None, "load.return_value": None}
    pipeline.configure_mock(**attrs)
    tester = LocalPredictor(pipeline)
    got = tester.predict(Path(__file__))
    assert got.licenses[0] == "MIT"
    assert got.filename == str(Path(__file__))


@patch('rigel.cli.prediction_logic.post', side_effect=mock_post)
def test_predict_server(mocked_post):
    # maybe test request payload
    api_endpoint = Mock()
    tester = ServerPredictor(api_endpoint)
    got = tester.predict(Path(__file__))
    assert mocked_post.called == 1
    assert got.licenses[0] == "MIT"
    assert got.filename == str(Path(__file__))


@patch("rigel.cli.prediction_logic.post", return_value=FakeResponse("", 500))
def test_invalid_response(mocked_post):
    with pytest.raises(PredictionLogicException):
        api_endpoint = Mock()
        tester = ServerPredictor(api_endpoint)
        got = tester.predict(Path(__file__))


@patch('rigel.cli.prediction_logic.post', side_effect=PredictionLogicException)
def test_no_network(mocked_post):
    api_endpoint = Mock()
    with pytest.raises(PredictionLogicException):
        tester = ServerPredictor(api_endpoint)
        tester.predict(Path(__file__))


def test_invalid_path():
    with pytest.raises(FileNotFoundError):
        pipeline = Mock()
        tester = LocalPredictor(pipeline)
        tester.predict("invalid path")
