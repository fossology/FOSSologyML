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
import pytest
import rigel
from pathlib import Path
from rigel.pipeline.preprocessor.comment_extractor import extract_comments_and_strings
from rigel.pipeline.enums import *

base_path = Path(Path(__file__).parent / "test_data")
file_names = ['html.html', 'c.c', 'c_plus_plus.cpp', 'python.py', 'shell.sh', 'xml.xml', "php.php",
              "error_file.scratch"]
file_types = [MimeType.HTML, MimeType.C, MimeType.C_PLUS_PLUS, MimeType.PYTHON, MimeType.SHELL, MimeType.XML,
              MimeType.PHP, MimeType.UNKNOWN]
complete_result = [['This is title', '\n\nHello world\n\n'],
                   ['printf() displays the string inside quotation', 'Hello, World!'],
                   ['\nMultiline test: This is a test comment\n\nsingle line text', 'Hello, World!'],
                   ['!/usr/bin/env python\n-*- encoding: utf-8 -*-', '"', '"',
                    '\nThis is a\nmulti\nline\ncomment\n\nThis is a single line comment!', 'Hello, world!'],
                   ['!/bin/sh\nThis is a comment!'],
                   ['xml version="1.0" encoding="UTF-8"?', 'hello world'],
                   ['string',
                    "Declare the variable 'string' and assign it a value.\nThe <br> is the HTML equivalent to a new line.",
                    'Hello World!<br>', '%s'], []]


def retrive_file(name):
    with open(Path(base_path / name), 'r') as file:
        result = file.read()
    return result


@pytest.mark.parametrize("testinputs, expected, file_type", zip(file_names, complete_result, file_types))
def test_extract_comments_and_strings(testinputs, expected, file_type):
    testinputs = retrive_file(testinputs)
    got = extract_comments_and_strings(testinputs, file_type, include_strings=True)
    print(got)
    assert got == expected
