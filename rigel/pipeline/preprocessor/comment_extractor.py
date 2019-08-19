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
""""
Extracts all comments and all the strings for a single source file based on the MIME type of the file
"""

"""
License header and a substantial portion of the code taken from https://github.com/kelvintaywl/code_comment
MIT License

Copyright (c) 2017 Tay Wee Leng Kelvin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import re
from typing import Union

from bs4 import BeautifulSoup, NavigableString
from bs4 import Comment as SoupComment

from rigel.pipeline.enums import MimeType

logger = logging.getLogger(__name__)


class CommentNotTerminated(Exception):
    """ Error when detected comment was not terminate cleanly. """
    pass


class CodeLanguageUnsupported(Exception):
    """ Error when detected code language is not supported. """
    pass


class Comment:

    def __init__(self, body: list, start_line: int, end_line: int):
        self._body = body
        self.start_line = start_line
        self.end_line = end_line
        self.is_multiline = not start_line == end_line

    @staticmethod
    def parse(body: str, start_line: int = 0, end_line=0):
        return Comment(body.splitlines(), start_line, end_line)

    @property
    def line_number_str(self) -> str:
        if not self.start_line == self.end_line:
            return '{}~{}'.format(self.start_line, self.end_line)

        return str(self.end_line)

    @property
    def last_line_number(self) -> int:
        return self.end_line

    @property
    def body_str(self) -> str:
        return '\n'.join(self._body)

    def append(self, new_comment: 'Comment'):
        """
        Merge another comment onto this one, forming a single multiline comment literal.
        The original comment literal (self) is changed in place and can not be retrieved afterwards.
        :param new_comment:
        """

        self._body.extend(new_comment._body)
        self.end_line = new_comment.end_line
        self.is_multiline = True

    def __str__(self):
        return self.body_str


class StringLiteral:

    def __init__(self, text: str, line_number: Union[int, list] = 0):
        self.text = text
        self._line_number = line_number

    @property
    def line_number_str(self) -> str:
        if isinstance(self._line_number, list):
            return '{}~{}'.format(*self._line_number)

        return str(self._line_number)

    @property
    def last_line_number(self) -> Union[int, list]:
        if isinstance(self._line_number, list):
            return self._line_number[-1]
        return self._line_number

    def __str__(self):
        return self.text


class CodeLanguage:
    HTML = 'html'
    PYTHON = 'python'
    PHP = 'php'
    XML = 'xml'
    SGML = 'sgml'
    STANDARD = 'standard'
    SHELL = 'shell'
    PHP = 'php'

    @staticmethod
    def factory(code_name: str):
        if code_name == CodeLanguage.PYTHON:
            return PythonCodeLanguage
        elif code_name == CodeLanguage.PHP:
            return PHPCodeLanguage
        elif code_name == CodeLanguage.SGML:
            return SGMLCodeLanguage
        elif code_name == CodeLanguage.HTML:
            return HTMLCodeLanguage
        elif code_name == CodeLanguage.XML:
            return XMLCodeLanguage
        elif code_name == CodeLanguage.STANDARD:
            return BaseCodeLanguage
        elif code_name == CodeLanguage.SHELL:
            return ShellCodeLanguage
        elif code_name == CodeLanguage.PHP:
            return PHPCodeLanguage


class BaseCodeLanguage(CodeLanguage):
    # header, footer prefixes/suffixes
    SINGLE_LINE_COMMENT = ('//', None)
    # header, middle, footer prefixes/suffixes
    MULTI_LINE_COMMENT = ('/*', None, '*/')
    STRING = ['\"']

    def parse(self, content: str, include_strings: bool) -> iter:
        slc_header, slc_footer = self.SINGLE_LINE_COMMENT
        mlc_header, mlc_middle, mlc_footer = (None, None, None)
        if self.MULTI_LINE_COMMENT:
            mlc_header, mlc_middle, mlc_footer = self.MULTI_LINE_COMMENT
            has_multiline = True
        else:
            has_multiline = False

        # to hold current multiline comment info temporarily;
        # empty if parser not on multiline comment
        multiline_comment_buffer = []

        def is_currently_multi_line_comment():
            return has_multiline and bool(multiline_comment_buffer)

        def is_single_line_comment(text):
            return (not is_currently_multi_line_comment()
                    and text.startswith(slc_header)
                    and not slc_footer)

        def is_single_line_comment_multiline_notation(text):
            return (has_multiline
                    and (not is_currently_multi_line_comment()
                         and text.startswith(mlc_header)
                         and text.endswith(mlc_footer)
                         and len(text) >= len(mlc_header + mlc_footer))
                    )

        def is_multi_line_comment_start(text):
            return (has_multiline
                    and (not is_currently_multi_line_comment()
                         and text.startswith(mlc_header))
                    )

        def is_multi_line_comment_midst(text):
            return (has_multiline
                    and (is_currently_multi_line_comment()
                         and not text.startswith(mlc_header)
                         and not text.endswith(mlc_footer)
                         and (not mlc_middle or text.startswith(mlc_middle)))
                    )

        def is_multi_line_comment_end(text):
            return (has_multiline
                    and (is_currently_multi_line_comment()
                         and text.endswith(mlc_footer))
                    )

        for line_number, text in enumerate([l.strip() for l in content.splitlines()], start=1):
            if not text:
                continue

            if is_single_line_comment(text):
                comment_text = text.split(slc_header)[1].strip()
                yield Comment([comment_text], line_number, line_number)

            elif is_single_line_comment_multiline_notation(text):
                comment_text = text.split(mlc_header)[1]
                comment_text = comment_text.rsplit(mlc_footer)[0].strip()
                yield Comment([comment_text], line_number, line_number)

            elif has_multiline:
                if is_multi_line_comment_start(text):
                    comment_text = text.split(mlc_header)[1].strip()
                    multiline_comment_buffer.append([comment_text, line_number])

                elif is_multi_line_comment_midst(text):
                    comment_text = text
                    if mlc_middle:
                        comment_text = text.split(mlc_middle)[1].strip()
                    multiline_comment_buffer.append([comment_text, line_number])

                elif is_multi_line_comment_end(text):
                    comment_text = text.rsplit(mlc_footer)[0].strip()
                    multiline_comment_buffer.append([comment_text, line_number])
                    comment_texts, line_numbers = zip(*multiline_comment_buffer)
                    multiline_comment_buffer = []
                    yield Comment(list(comment_texts), line_numbers[0], line_numbers[-1])

            if include_strings:
                for quotes in self.STRING:
                    string_text = re.findall('{0}(.*(?<!\\))){0}'.format(quotes), text, re.I | re.M)
                    for s in string_text:
                        yield StringLiteral(s, line_number)


class PHPCodeLanguage(BaseCodeLanguage):
    # NOTE: assuming PHPDoc style
    MULTI_LINE_COMMENT = ('/**', '*', '*/')
    STRING = ['\"', '\'']


class SGMLCodeLanguage(BaseCodeLanguage):
    def parse(self, content: str, include_strings: bool) -> iter:
        soup = BeautifulSoup(content, "lxml")
        comments = list(map(Comment.parse, soup.find_all(string=lambda text: isinstance(text, SoupComment))))
        strings = list(map(StringLiteral, soup.find_all(string=lambda text: (isinstance(text, NavigableString)
                                                                             and not isinstance(text, SoupComment)
                                                                             and not str(text) == '\n'))))
        if include_strings:
            return iter(comments + strings)
        return iter(comments)


class HTMLCodeLanguage(SGMLCodeLanguage):
    pass


class XMLCodeLanguage(SGMLCodeLanguage):
    pass


class PythonCodeLanguage(BaseCodeLanguage):
    SINGLE_LINE_COMMENT = ('#', None)
    MULTI_LINE_COMMENT = ('"""', None, '"""')
    STRING = ['\"', '\'']


class ShellCodeLanguage(BaseCodeLanguage):
    SINGLE_LINE_COMMENT = ('#', None)
    MULTI_LINE_COMMENT = None
    STRING = ['\"', '\'']


class Parser:
    SUPPORTED_FILE_TYPES = {
        MimeType.C: CodeLanguage.STANDARD,
        MimeType.C_PLUS_PLUS: CodeLanguage.STANDARD,
        MimeType.JAVA: CodeLanguage.STANDARD,
        MimeType.HTML: CodeLanguage.HTML,
        MimeType.XML: CodeLanguage.XML,
        MimeType.SGML: CodeLanguage.SGML,
        MimeType.PYTHON: CodeLanguage.PYTHON,
        MimeType.SHELL: CodeLanguage.SHELL,
        MimeType.PHP: CodeLanguage.PHP
    }

    def __init__(self, content, type, include_strings):
        self.content = content
        self.include_strings = include_strings
        supported = False
        for t in self.SUPPORTED_FILE_TYPES:
            if t == type:
                self.code_language = CodeLanguage.factory(self.SUPPORTED_FILE_TYPES.get(t))
                supported = True
                break
        if not supported:
            raise CodeLanguageUnsupported

    def __iter__(self):
        return self.parse()

    def parse(self):
        return self.code_language.parse(self.code_language, self.content, self.include_strings)


def extract(content: str, type: str, include_strings: bool) -> iter:
    return Parser(content, type, include_strings)


def extract_comments_and_strings(content: str, type: str, include_strings: bool = True,
                                 collapse_singleline_comments: bool = True) -> list:
    try:
        parsed_content = list(Parser(content, type, include_strings))
    except CodeLanguageUnsupported:
        logger.debug(f'Could not extract comments or strings for {type}')
        return []

    if collapse_singleline_comments:
        strings = []
        comments = []
        for item in parsed_content:
            if isinstance(item, Comment):
                comments += [item]
            else:
                strings += [item]
        comments = do_collapse_singleline_comments(comments)

        parsed_content = strings + comments
        parsed_content.sort(key=lambda x: x.last_line_number)

    result = [str(item) for item in parsed_content]
    return result


def do_collapse_singleline_comments(comments: list):
    result = []
    iterator = iter(comments)
    finished = False

    try:
        comment = next(iterator)
    except StopIteration:
        return result

    while not finished:
        try:
            next_comment = next(iterator)

            if next_comment.start_line - comment.end_line <= 1:
                comment.append(next_comment)
                continue

            result.append(comment)
            comment = next_comment

        except StopIteration:
            result.append(comment)
            finished = True

    return result


if __name__ == '__main__':
    pass
