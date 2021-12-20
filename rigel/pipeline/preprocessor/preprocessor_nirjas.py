#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2021, Siemens AG
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
The preprocessor extracts comments from given file using Nirjas library and extracts license related
words for making prediction of the license that the file contains.
"""
import spacy

from rigel.pipeline.preprocessor.preprocessor import Preprocessor
from rigel.pipeline.preprocessor import Nirjas_comments

class PreprocessorNirjas(Preprocessor):
    def process_license_relevant_words(self,  file_path, raw_text: str) -> list:
        """
        TODO
        :param file_type:
        :param raw_text:
        :return:
        """
        if not raw_text:
            return []

        comments_and_strings = Nirjas_comments.extract(file_path)
        if comments_and_strings:
            cleaned_text = self.extract_license_related_text(comments_and_strings)
            return self.process_text(cleaned_text)

    def process_no_license_relevant_words(self, file_path, raw_text: str) -> list:
        """
        TODO
        :param file_type:
        :param raw_text:
        :return:
        """
        if not raw_text:
            return []

        comments_and_strings = Nirjas_comments.extract(file_path)
        if comments_and_strings:
            no_lrw_text = self.extract_no_license_related_text(comments_and_strings)
            return self.process_text(no_lrw_text)

    def process(self, file_path, raw_text) -> list:
        """
        TODO
        :param file_type:
        :param raw_text:
        :return:
        """
        if not raw_text:
            return []

        license_related_words = self.process_license_relevant_words(file_path, raw_text)
        if license_related_words:
            return license_related_words
        else:
            return self.process_text(raw_text)

    def __init__(self):
        self.nlp = spacy.load('en', disable=['parser', 'tagger', 'entityrecognizer', 'ner', 'textcat'])
        self.nlp.max_length = 2 * 10**6
        self.nlp.Defaults.stop_words -= self.relevant_stop_words

    def process_text(self, text: str) -> list:
        """
        Calls text processing functions
        :param text:
        :return: list of processed text tokens
        """

        if not text:
            return []

        if len(text) > self.nlp.max_length:
            # TODO handle this nicer
            return []

        def filter_token(token):
            return token.is_alpha or token.is_digit

        tokens = self.nlp(text)
        processed_text = [token.lemma_.lower() for token in tokens if filter_token(token)]
        return processed_text