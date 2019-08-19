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
The Dataloader serves as a custom option to save various sklearn objects in a space efficient format without having to
rely on pickle
"""

import json
import logging
import os
import time
from enum import Enum
from pathlib import Path

import h5py as h5
import numpy as np
import scipy.sparse as sp
from sklearn.base import BaseEstimator
from sklearn.externals import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import ClassifierChain
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.svm import LinearSVC

logger = logging.getLogger(__name__)


class ClassifTypes(Enum):
    endings = ['_le', "_me", "_ve", "_ls", "_mn", "_cc"]
    lookup = {TfidfVectorizer: '_ve', ClassifierChain: "_cc", MultinomialNB: "_mn", MultiLabelBinarizer: '_me',
              LabelEncoder: '_le', LinearSVC: "_ls"}

    def __str__(self):
        return str(self.value)


class IoDecorator:

    @staticmethod
    def save_params(save_function):
        def wrapper(*args):
            self = args[0]
            params = args[1].get_params()
            #  convert to native python datatypes and check for serializabilty
            for key, value in list(params.items()):
                if type(value).__module__ == np.__name__:
                    params[key] = value.item()
                elif not isinstance(value, (int, float, bool, list, tuple, dict)):
                    del params[key]
            filename = args[2] + '.json'
            with open(Path(self.path / ('params_' + filename)), 'w', encoding='utf8') as param_doc:
                json.dump(params, param_doc)

            return save_function(*args)

        return wrapper

    @staticmethod
    def load_params(load_function):
        def wrapper(*args):
            self = args[0]
            filename = args[1]
            with open(Path(self.path / ('params_' + filename + ".json")), mode='rb') as param_doc:
                params = json.load(param_doc)
            res = load_function(*args)
            res.set_params(**params)
            return res
        return wrapper

    @staticmethod
    def log_time(timed_function):
        def wrapper(*args):
            start = time.time()
            res = timed_function(*args)
            end = time.time()
            logger.info(f"It took {start-end} seconds to execute the action")
            return res
        return wrapper

    @staticmethod
    def log_size(filemod):
        def _log_size_dec(save_function):
            def wrapper(*args):
                self = args[0]
                save_function(*args)
                mod_fileanme = filemod(args[2])
                size = os.path.getsize(Path(self.path / mod_fileanme))
                logger.info(f"it took {size} mb to save {mod_fileanme}")
                return
            return wrapper
        return _log_size_dec


class DataLoaderCustom:
    """Implements the custom save methods as described in the file header"""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.types = ClassifTypes.endings.value
        self.pickler = DataLoaderPikle(self.path)
        self.save_functions = [self.save_labelencoder,
                               self.save_labelencoder,
                               self.save_vectorizer,
                               self.save_svc,
                               self.save_multinb,
                               self.save_chain_classifier]
        # label encoder and multi label binarizer can use the same loading functions(labelencoder)
        self.load_functions = [self.load_labelencoder,
                               self.load_labelencoder,
                               self.load_vectorizer,
                               self.load_svc,
                               self.load_multinb,
                               self.load_chain_classifier]

    @staticmethod
    def _get_filename_suffix(filename: str):
        return filename[-3:]

    @staticmethod
    def _get_estimator_suffix(filename: str):
        return filename[-6: -3]

    def save(self, item: object, filename: str):
        """Acts as a proxy to distribute the tasks to the different functions.
        The file suffix is used to determine which kind of objects needs to be saved
        :param item: sklearn object to be saved
        :param filename: the filename of the saved object with the correct suffix. The correct suffix can be found in the enums"""
        suffix = self._get_filename_suffix(filename)
        if suffix in self.types:
            save_function = self.save_functions[self.types.index(suffix)]
            save_function(item, filename)
        else:
            self.pickler.save(item, filename)

    def load(self, filename: str):
        suffix = self._get_filename_suffix(filename)
        if suffix in self.types:
            load_function = self.load_functions[self.types.index(suffix)]
            return load_function(filename)
        else:
            return self.pickler.load(filename)

    @IoDecorator.save_params
    def save_vectorizer(self, vectorizer: TfidfVectorizer, filename: str):
        vocab = vectorizer.vocabulary_
        vocab = {key: value.item() for key, value in vocab.items()}
        with open(Path(self.path / ('vocabulary_' + filename)), 'w', encoding='utf8') as outfile:
            json.dump(vocab, outfile)
        np.save(Path(self.path / ("idfs_" + filename)), vectorizer.idf_, allow_pickle=False)

    @IoDecorator.load_params
    def load_vectorizer(self, filename: str) -> TfidfVectorizer:
        idfs = np.load(Path(self.path / ("idfs_" + filename + '.npy')))

        class WrapperVectorizer(TfidfVectorizer):
            TfidfVectorizer.idf_ = idfs

        vectorizer = WrapperVectorizer()
        vectorizer._tfidf._idf_diag = sp.spdiags(idfs, diags=0, m=len(idfs), n=len(idfs))
        vocabulary = json.load(open(Path(self.path, 'vocabulary_' + filename), mode='rb'))
        vectorizer.vocabulary_ = {key: np.int64(value) for key, value in vocabulary.items()}
        vectorizer.__class__ = TfidfVectorizer
        return vectorizer

    @IoDecorator.save_params
    def save_labelencoder(self, le: BaseEstimator, filename: str) -> None:
        converted = np.array(le.classes_, dtype=str)
        np.save(Path(self.path / filename), converted, allow_pickle=False)

    @IoDecorator.load_params
    def load_labelencoder(self, filename: str) -> LabelEncoder:
        if self._get_filename_suffix(filename) == '_le':
            encoder = LabelEncoder()
        else:
            encoder = MultiLabelBinarizer()
        filename += ".npy"
        encoder.classes_ = np.load(Path(self.path / filename))
        return encoder

    @IoDecorator.save_params
    def save_svc(self, svm: LinearSVC, filename: str) -> None:
        store = h5.File(Path(self.path / filename), 'w')
        store['coefficients'] = svm.coef_
        store['intercepts'] = svm.intercept_
        store['classes'] = svm.classes_
        store.close()

    @IoDecorator.load_params
    def load_svc(self, filename: str) -> LinearSVC:
        store = h5.File(Path(self.path / filename), 'r')
        coefs = store['coefficients'][:]
        intercepts = store['intercepts'][:]
        classes = store['classes'][:]
        store.close()
        svc = LinearSVC()
        svc.coef_ = coefs
        svc.intercept_ = intercepts
        svc.classes_ = classes
        return svc

    @IoDecorator.save_params
    def save_multinb(self, clf: MultinomialNB, filename: str) -> None:
        store = h5.File(Path(self.path / filename), 'w')
        store['classes'] = clf.classes_
        store['coefficients'] = clf.coef_
        store['class_log_prior'] = clf.class_log_prior_
        store['intercepts'] = clf.intercept_
        store['feature_log_prob'] = clf.feature_log_prob_
        store.close()

    @IoDecorator.load_params
    def load_multinb(self, filename: str) -> MultinomialNB:
        store = h5.File(Path(self.path / filename), 'r')
        classes = store['classes'][:]
        coef = store['coefficients'][:]
        intercept = store['intercepts'][:]
        class_log_prior = store['class_log_prior'][:]
        feature_log_prob = store['feature_log_prob'][:]

        class WrapperMultinomialNB(MultinomialNB):
            MultinomialNB.coef_ = coef
            MultinomialNB.classes_ = classes
            MultinomialNB.intercept_ = intercept
            MultinomialNB.class_log_prior_ = class_log_prior
            MultinomialNB.feature_log_prob_ = feature_log_prob

        mnb = WrapperMultinomialNB()
        return mnb

    @IoDecorator.save_params
    def save_chain_classifier(self, cc: ClassifierChain, filename: str):
        # model_path = Path(self.path / Path(filename))
        # model_path.mkdir(exist_ok=True)
        store = h5.File(Path(self.path / filename), 'w')
        store['classes'] = cc.classes_
        store['order'] = cc.order_
        store.close()
        estimatorsuffix = self._get_estimator_suffix(filename)
        for counter, classifier in enumerate(cc.estimators_):
            sub_filename = filename + "_sub_estimator_" + str(counter) + estimatorsuffix
            self.save(classifier, sub_filename)

    @IoDecorator.load_params
    def load_chain_classifier(self, filename: str) -> ClassifierChain:
        store = h5.File(Path(self.path / filename), 'r')
        classes_ = store['classes'][:]
        order = store['order'][:]
        store.close()
        estimators = []
        res = ClassifierChain(LinearSVC())  # Linear SVC is used as a placeholder(other options: metaclasses, __new__)
        estimatorsuffix = self._get_estimator_suffix(filename)
        for counter in range(len(classes_)):
            sub_filename = filename + "_sub_estimator_" + str(counter) + estimatorsuffix
            estimators.append(self.load(sub_filename))
        res.classes_ = classes_
        res.order_ = order
        res.estimators_ = estimators
        return res

    @staticmethod
    def determine_suffix(sktype) -> str:
        suffix = ClassifTypes.lookup.value[type(sktype)]
        if suffix == '_cc':
            add_suffix = DataLoaderCustom.determine_suffix(sktype.estimators_[0])
            suffix = add_suffix + suffix
        return suffix


class DataLoaderPikle:
    """Acts as a replacement for the custom dataloader in case there is no custom implementation for the object"""

    def __init__(self, path):
        self.path = path

    def save(self, item: object, filename: str):
        joblib.dump(item, Path(self.path / (filename + ".sav")))

    def load(self, filename: str):
        loaded_model = joblib.load(Path(self.path / (filename + ".sav")))
        return loaded_model
