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
The Preprocessor prepares the data for the vectorizer. It first splits the sentence into tokens, converts them to lower
case and removes non alpha numeric characters. Then whitespaces and stopwords are filtered and the stem(porter stemming)
is returned.
"""
import re

import nltk.stem
import nltk.tokenize

from rigel.pipeline.preprocessor.preprocessor import Preprocessor


class PreprocessorNltk(Preprocessor):

    def remove_stopwords(self, list_in: list) -> list:
        """
        Removes stopwords: words that are frequent but without valuable semantic meaning.
        Important words (see src/data/analyze_stopwords.py) are preserved
        :param list_in:
        :return:
        """
        standard_en_stopwords = set(nltk.corpus.stopwords.words('english'))

        my_stopwords = standard_en_stopwords - self.relevant_stop_words

        list_out = [word for word in list_in if word not in my_stopwords]
        return list_out

    def remove_special_characters(self, list_in: list, regex: str = '') -> list:
        """
        Removes (deletes) characters matched by provided regex
        :param list_in:
        :param regex:
        :return:
        """
        if not regex:
            regex = '[^0-9a-zA-Z\.]'
        list_out = [re.sub(regex, '', word) for word in list_in]
        return list_out

    def remove_whitespace_elements(self, list_in: list) -> list:
        """
        Removes all lines which contain only whitespace characters, tabs etc
        :param list_in:
        :return:
        """
        list_out = [word for word in list_in if ''.join(word.split())]
        return list_out

    def text_to_lowercase(self, list_in: list) -> list:
        """
        All strings to lowercase
        :param list_in:
        :return:
        """
        list_out = [word.lower() for word in list_in]
        return list_out

    def stem_text(self, list_in: list, stemmer: nltk.stem.api.StemmerI = nltk.stem.PorterStemmer()) -> list:
        """
        http://www.nltk.org/api/nltk.stem.html
        :param stemmer:
        :param list_in:
        :return:
        """
        list_out = [stemmer.stem(word) for word in list_in]
        return list_out

    def tokenize(self, text: str) -> list:
        """
        http://www.nltk.org/api/nltk.tokenize.html
        :return:
        """
        return nltk.tokenize.word_tokenize(text)

    def process_text(self, text: str) -> list:
        """
        Calls text processing functions in a sequence
        :param text:
        :return:
        """

        if not text:
            return []

        text = self.tokenize(text)
        text = self.text_to_lowercase(text)
        text = self.remove_special_characters(text)
        text = self.remove_whitespace_elements(text)
        text = self.remove_stopwords(text)
        text = self.stem_text(text)

        return text
