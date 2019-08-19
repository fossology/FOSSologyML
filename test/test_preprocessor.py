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

import nltk
import pytest
from rigel.pipeline.preprocessor.preprocessor import Preprocessor
from rigel.pipeline.preprocessor.preprocessor_spacy import PreprocessorSpacy
from rigel.pipeline.preprocessor.preprocessor_nltk import PreprocessorNltk
from pathlib import Path
import time


@pytest.fixture()
def preprocessor_nltk():
    return PreprocessorNltk()


@pytest.fixture()
def preprocessor_spacy():
    return PreprocessorSpacy()


@pytest.fixture(params=['preprocessor_nltk', 'preprocessor_spacy'])
def implementation(request):
    return request.getfixturevalue(request.param)


@pytest.fixture()
def stop_words():
    return set(nltk.corpus.stopwords.words('english'))


@pytest.fixture()
def full_stop_words():
    return ['yourselves', 'myself', 'ourselves', 'hers', 'off', 'herself']


@pytest.fixture()
def special_characters():
    return ['@b#$', "a!_)#$"]


@pytest.fixture()
def white_spaces():
    return ['     ', "  ", "        "]


@pytest.fixture()
def empty_input():
    return ['', "   ", None]


class TestSubMethodsPreprocessor:

    @staticmethod
    def test_remove_stopwords(full_stop_words, preprocessor_nltk):
        got = preprocessor_nltk.remove_stopwords(full_stop_words)
        expected = []
        assert got == expected

    @staticmethod
    def test_special_character(special_characters, preprocessor_nltk):
        got = preprocessor_nltk.remove_special_characters(special_characters)
        expected = ['b', 'a']
        assert got == expected

    @staticmethod
    def test_remove_whitespace(white_spaces, preprocessor_nltk):
        got = preprocessor_nltk.remove_whitespace_elements(white_spaces)
        expected = []
        assert got == expected

    @staticmethod
    def test_tokenize(preprocessor_nltk):
        sample_sentence = "This is a blessing License."
        expected = ["This", "is", 'a', 'blessing', "License", "."]
        got = preprocessor_nltk.tokenize(sample_sentence)
        assert got == expected


class TestCompletePreprocessor:
    sample_sentence = "This is a sample sentence with @ $characters -_). This is my second !@#$%^&&*()_. AND third"

    @staticmethod
    def test_complete_process_spacy(preprocessor_spacy):
        got = preprocessor_spacy.process_text(TestCompletePreprocessor.sample_sentence)
        expected = ['this', 'be', 'a', 'sample', 'sentence', 'with', 'character', 'this', 'be', 'my', '2', 'and', '3']
        assert got == expected

    @staticmethod
    def test_complete_process_nltk(preprocessor_nltk):
        got = preprocessor_nltk.process_text(TestCompletePreprocessor.sample_sentence)
        expected = ['thi', 'is', 'a', 'sampl', 'sentenc', 'with', 'charact', '.', 'thi', 'is', 'my', 'second', '.', 'and', 'third']
        assert got == expected

    @staticmethod
    def test_empty_input(implementation, empty_input):
        for sample_input in empty_input:
            got = implementation.process_text(sample_input)
            assert got == []

    @staticmethod
    def test_process_raw_text_has_no_generic_implementation():
        with pytest.raises(TypeError):
            a = Preprocessor()

    @staticmethod
    @pytest.mark.skip(reason="needs specific dataset and is just there for comparing speeds")
    def test_speed(implementation):
        now = time.time()
        with open(Path(r"C:\Users\Sven\Documents\datasets\books-of-friedrich-nietzsche\test1.txt"), "r") as best_of_nietzsche:
            for line in best_of_nietzsche:
                implementation.process_text(line)
        then = time.time()
        dur1 = then-now
        print(dur1)




