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

import re
from pathlib import Path
from unittest.mock import patch
import platform
import pytest
from rigel.pipeline.enums import MimeType
from rigel.utils import get_file_type_from_stream, get_file_type_from_path

test_dir = Path(__file__).resolve().parents[0]
file_type_test_data = [
    (test_dir / 'test_data' / 'c.c', MimeType.C),
    (test_dir / 'test_data' / 'c_plus_plus.cpp', MimeType.C_PLUS_PLUS),
    (test_dir / 'test_data' / 'html.html', MimeType.HTML),
    (test_dir / 'test_data' / 'xml.xml', MimeType.XML),
    (test_dir / 'test_data' / 'shell.sh', MimeType.SHELL),
    (test_dir / 'test_data' / 'python.py', MimeType.PYTHON),
    (test_dir / 'test_data' / 'java.java', MimeType.JAVA)
]


@pytest.mark.skipif(platform.system() == "Windows", reason="Tests cannot succeed on windows")
class TestGetFileTypeFromPath:

    @staticmethod
    @pytest.mark.parametrize('file_path, file_type_regex', file_type_test_data)
    def test_from_path(file_path, file_type_regex):
        expected = file_type_regex
        result = get_file_type_from_path(file_path)
        assert expected == result

    @staticmethod
    def test_from_path_throws_on_non_existing_path(tmpdir):
        not_existing_path = Path(tmpdir / 'not_existing_file')
        expected_error = 'No such file or directory'

        with pytest.raises(FileNotFoundError) as e:
            get_file_type_from_path(not_existing_path)

        assert expected_error == e.value.strerror


class TestGetFileTypeFromStream:

    @staticmethod
    @pytest.mark.skipif(platform.system() == "Windows",
                        reason="Tests cannot succeed on windows (python-magic lib only available on unix")
    @pytest.mark.parametrize('file_path, file_type_regex', file_type_test_data)
    def test_from_stream(file_path, file_type_regex):
        with open(file_path) as file:
            stream = file.read(1024)
        expected = file_type_regex
        result = get_file_type_from_stream(stream)

        assert expected == result

    @staticmethod
    def test_from_stream_handles_missing_import():
        with patch('magic.from_buffer', side_effect=ImportError()):
            expected = MimeType.UNKNOWN
            result = get_file_type_from_stream("")

        assert expected == result

    @staticmethod
    def test_from_stream_handles_empty_file_stream():
        expected = MimeType.UNKNOWN
        result = get_file_type_from_stream("")

        assert expected == result

    @staticmethod
    def test_from_stream_handles_null_file_stream():
        expected = MimeType.UNKNOWN
        result = get_file_type_from_stream(None)

        assert expected == result
