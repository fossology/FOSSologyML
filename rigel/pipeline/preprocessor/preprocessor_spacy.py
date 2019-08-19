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
The Preprocessor prepares the data for the vectorizer. It first removes stopwords and non alphanumeric characters. In
the next step the lemma of the word is taken.
"""

import spacy

from rigel.pipeline.preprocessor.preprocessor import Preprocessor


class PreprocessorSpacy(Preprocessor):

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