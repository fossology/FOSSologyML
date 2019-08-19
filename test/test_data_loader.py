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

import numpy as np
import pytest
from numpy.testing import assert_array_equal
from rigel.pipeline.dataloader.data_loader import DataLoaderCustom, DataLoaderPikle
from sklearn.datasets import make_classification, make_multilabel_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.multioutput import ClassifierChain
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.svm import LinearSVC


@pytest.fixture()
def pikle(tmpdir):
    return DataLoaderPikle(tmpdir)


@pytest.fixture()
def custom(tmpdir):
    return DataLoaderCustom(tmpdir)


@pytest.fixture(params=['pikle', 'custom'])
def implementation(request):
    return request.getfixturevalue(request.param)


class TestEncoder:

    @staticmethod
    def test_labelencoder(implementation):
        name = 'testlabelencoder_le'
        le = LabelEncoder()
        le.fit(['a', 'b', 'b', 'c'])
        expected = le.transform(['a', 'a', 'b', 'c'])
        implementation.save(le, name)
        test_le = implementation.load(name)
        got = test_le.transform(['a', 'a', 'b', 'c'])
        assert_array_equal(got, expected)

    @staticmethod
    def test_multilabelencoder(implementation):
        name = 'testmulilabelencoder_me'
        valid_me = MultiLabelBinarizer()
        valid_me.fit([('a', 'b'), ('c',)])
        implementation.save(valid_me, name)
        test_me = implementation.load(name)
        got = test_me.transform([('a',)])
        expected = valid_me.transform([('a',)])
        assert_array_equal(got, expected)
        # test inverse transform
        print(expected)
        inverse_expected = valid_me.inverse_transform(expected)
        print(got)
        inverse_got = test_me.inverse_transform(got)
        assert_array_equal(inverse_got, inverse_expected)


class TestVectorizer:

    @staticmethod
    @pytest.mark.skip('TODO seems to be a mismatch when saving loading the _tfidf.idf_ versus _idf- Only happens when the whole module is started')
    def test_vectorizer(implementation):
        name = "test_vectorizer_ve"
        test = ["this is a smile training she sang"]
        txt1 = ['His smile was not perfect', 'His smile was not not not not perfect', 'she not sang']
        valid_vectorizer = TfidfVectorizer(smooth_idf=False, sublinear_tf=False, norm=None, analyzer='word')
        valid_vectorizer.fit(txt1)
        implementation.save(valid_vectorizer, name)
        test_vectorizer = implementation.load(name)
        expected = valid_vectorizer.transform(test)
        got = test_vectorizer.transform(test)
        np.allclose(got.A, expected.A)


class TestClassifier:

    @staticmethod
    def test_svm(implementation):
        name = "test_linearsvc_ls"
        x, y = make_classification(n_features=4, random_state=0)
        valid_linearsvc = LinearSVC(random_state=0)
        valid_linearsvc.fit(x, y)
        implementation.save(valid_linearsvc, name)
        test_linearsvc = implementation.load(name)
        expected = valid_linearsvc.predict([[0, 0, 0, 0]])
        got = test_linearsvc.predict([[0, 0, 0, 0]])
        assert_array_equal(got, expected)

    @staticmethod
    def test_multinb(implementation):
        name = "test_multinb_mn"
        x = np.random.randint(5, size=(6, 100))
        y = np.array([1, 2, 3, 4, 5, 6])
        valid_mnb = MultinomialNB()
        valid_mnb.fit(x, y)
        implementation.save(valid_mnb, name)
        test_mnb = implementation.load(name)
        got = test_mnb.predict(x[2:3])
        expected = valid_mnb.predict(x[2:3])
        assert_array_equal(got, expected)

    @staticmethod
    def test_randomforest(implementation):
        name = "test_rf"
        x, y = make_classification(n_samples=1000, n_features=4,
                                   n_informative=2, n_redundant=0,
                                   random_state=0, shuffle=False)
        valid_rf = RandomForestClassifier(max_depth=2, random_state=0)
        valid_rf.fit(x, y)
        expected = valid_rf.predict([[0, 0, 0, 0]])
        implementation.save(valid_rf, name)
        test_rf = implementation.load(name)
        got = test_rf.predict([[0, 0, 0, 0]])
        assert_array_equal(got, expected)

    @staticmethod
    def test_chainclassifier(implementation):
        name = "test_ls_cc"
        x, y = make_multilabel_classification()
        x_train, x_test, y_train, y_test = train_test_split(x, y)
        valid_cc = ClassifierChain(LinearSVC())
        valid_cc.fit(x_train, y_train)
        implementation.save(valid_cc, name)
        test_cc = implementation.load(name)
        expected = valid_cc.predict(x_test)
        got = test_cc.predict(x_test)
        assert_array_equal(got, expected)


class TestInputError:

    @staticmethod
    def test_filenotfound(implementation):
        name = 'testmulilabelencoder_me'
        valid_me = MultiLabelBinarizer()
        valid_me.fit([('a', 'b'), ('c',)])
        implementation.save(valid_me, name)
        with pytest.raises(FileNotFoundError):
            implementation.load("dgrgdrgdrg")
            pass
