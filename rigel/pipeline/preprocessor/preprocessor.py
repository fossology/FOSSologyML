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

"""
TODO
"""

import logging
import re
from abc import ABC, abstractmethod

from rigel.pipeline.preprocessor import comment_extractor

logger = logging.getLogger(__name__)


class Preprocessor(ABC):
    """
    Abstract base class used to implement basic functionality.

    """
    LRW_PATTERN = re.compile(r'licen|copyright|\(c\)|public domain', re.IGNORECASE)

    relevant_stop_words = {'will', 'now', 'whom', 'them', 'own', 'above', 'her', 'themselves', 'are', 'too', 'i', 'nor',
                           'yours', 'more', 'few', 'most', 'ours', 'here', 'just', 'had', 'they', 'that', 'himself',
                           'a', 'same', 'about', 't', 'she', 'was', 'do', 'having', 'their', 'been', 'doing', 'not',
                           'being', 'the', 'very', 're', 'with', 'how', 'those', 'yourself', 'at', 'what', 'your', 'if',
                           'you', 'by', 's', 'then', 'as', 'to', 'through', 'it', 'there', 'so', 'other', 'during',
                           'up', 'out', 'we', 'for', 'where', 'once', 'd', 'when', 'under', 'between', 'against',
                           'these', 'he', 'him', 'in', 'does', 'of', 'all', 'or', 'no', 'his', 'but', 'only', 'such',
                           'were', 'some', 'again', 'should', 'over', 'and', 'why', 'an', 'which', 'me', 'this', 'into',
                           'be', 'o', 'have', 'y', 'has', 'is', 'than', 'because', 'did', 'my', 'am', 'can', 'before',
                           'down', 'any', 'on', 'after', 'below', 'from', 'until', 'itself', 'who', 'each', 'further',
                           'while', 'our', 'its', 'both'}

    @abstractmethod
    def process_text(self, text: str):
        pass

    def process_license_relevant_words(self, raw_text: str, file_type: str = comment_extractor.MimeType) -> list:
        """
        TODO
        :param file_type:
        :param raw_text:
        :return:
        """
        if not raw_text:
            return []

        comments_and_strings = comment_extractor.extract_comments_and_strings(raw_text, file_type, include_strings=True)
        if comments_and_strings:
            cleaned_text = self.extract_license_related_text(comments_and_strings)
            return self.process_text(cleaned_text)

    def process_no_license_relevant_words(self, raw_text: str, file_type: str = comment_extractor.MimeType) -> list:
        """
        TODO
        :param file_type:
        :param raw_text:
        :return:
        """
        if not raw_text:
            return []

        comments_and_strings = comment_extractor.extract_comments_and_strings(raw_text, file_type, include_strings=True)
        if comments_and_strings:
            no_lrw_text = self.extract_no_license_related_text(comments_and_strings)
            return self.process_text(no_lrw_text)

    def process(self, raw_text: str, file_type: str = comment_extractor.MimeType) -> list:
        """
        TODO
        :param file_type:
        :param raw_text:
        :return:
        """
        if not raw_text:
            return []

        license_related_words = self.process_license_relevant_words(raw_text, file_type)
        if license_related_words:
            return license_related_words
        else:
            return self.process_text(raw_text)

    @staticmethod
    def extract_license_related_text(literals: list, re_pattern=LRW_PATTERN) -> str:
        """
        Filters a list of strings and keeps only those elements that contain license relevant trigger words
        :param literals: the list to be filtered
        :param re_pattern: regex defining license relevant words
        :return: all literals where the regex found a match, concatenated to a single string
        """
        text = ''

        for literal in literals:
            if re_pattern.search(literal):
                text += literal
                text += '\n'

        return text

    @staticmethod
    def extract_no_license_related_text(literals: list, re_pattern=LRW_PATTERN) -> str:
        """
        Filters a list of strings and keeps only those elements that contain license relevant trigger words
        :param literals: the list to be filtered
        :param re_pattern: regex defining license relevant words
        :return: all literals where the regex found a match, concatenated to a single string
        """
        text = ''

        for literal in literals:
            if not re_pattern.search(literal):
                text += literal
                text += '\n'

        return text
