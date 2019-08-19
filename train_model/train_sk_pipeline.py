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
Script that creates a sklearn pipeline in following way:

There is one preclassifier in 1st stage that decides which of the 2a or 2b will be used in the second stage
1, single vs multi vs no_license problem with TF-IDF Vectorizer that includes samples from all 3 kinds of possible outputs, the max number of inputs per category was limited due to performance issues on our machine
2a,  single problem trained only on Single License Outputs: is used for prediction if 1st Classifier decides in its favor (can achieve high accuracies)
2b, multi problem using ChainClassifier with Support Vector Machine (linear kernel) as Basic Classifier:  is used for prediction if 1st Classifier decides in its favor

-each step uses TF-IDF Vectorizer, however for each step the word-count matrix is computed from the inputs that fit the problem scope. The 1- ,2- and 3-grams (collections of successive words) were selected as features with maximum cap of 10 000 features per classifier.
-each step employs Support Vector Machine (SVM)
"""

import datetime
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from configparser import ConfigParser
from os import cpu_count
from pathlib import Path

import numpy as np
from analyze_data import CollectionAnalysis
from database import MongoDB
from documents import Documents
from dotenv import load_dotenv, find_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import ClassifierChain
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.svm import LinearSVC
from utils import root_logger, add_file_handler_to_logger, get_train_dir, get_db_analysis_dir

from rigel.pipeline.dataloader.data_loader import DataLoaderCustom
from rigel.pipeline.enums import *
from rigel.pipeline.sk_pipeline import SKLearnProblem, SKLearnPipeline

logger = logging.getLogger(__name__)


def single_label(x_train, y_train, name="SP"):
    logger.info(f"Single label problem: [{name}] - {len(x_train)}... ")
    le = LabelEncoder()
    vct = get_new_vectorizer()

    logger.info(f"[{name}] Vectorizing inputs...")
    x_train = vct.fit_transform(x_train)
    logger.info(f"[{name}] Vectorizing outputs...")
    y_train = le.fit_transform(np.ravel(y_train))

    logger.info(f"[{name}] Data shapes:")
    logger.info(f"[{name}] x_train: {x_train.shape}")
    logger.info(f"[{name}] y_train: {y_train.shape}")

    model = LinearSVC(random_state=0)
    model.fit(x_train, y_train)

    return SKLearnProblem(name, le, model, vct)


def multi_label(x_train, y_train, name="MP"):
    logger.info(f"Multi label problem: [{name}] - {len(x_train)}... ")
    le = MultiLabelBinarizer(sparse_output=True)
    vct = get_new_vectorizer()

    logger.info(f"[{name}] Vectorizing inputs...")
    x_train = vct.fit_transform(x_train)
    logger.info(f"[{name}] Vectorizing outputs...")
    y_train = le.fit_transform(y_train)

    logger.info(f"[{name}] Data shapes:")
    logger.info(f"[{name}] x_train: {x_train.shape}")
    logger.info(f"[{name}] y_train: {y_train.shape}")

    model = ClassifierChain(LinearSVC(random_state=0))
    model.fit(x_train, y_train.todense())

    return SKLearnProblem(name, le, model, vct)


def single_multi_or_no_license(x_train_single, y_train_single, x_train_multi, y_train_multi, x_train_no_license,
                               y_train_no_license, name="DP"):
    logger.info(f"Single or Multi or No License problem: [{name}] - {len(x_train)}... ")
    le = LabelEncoder()
    vct = get_new_vectorizer()

    x_train, y_train = map_single_multi_no_license_to_single_problem(x_train_multi, x_train_no_license, x_train_single,
                                                                     y_train_multi, y_train_no_license, y_train_single)

    logger.info(f"[{name}] Vectorizing inputs...")
    x_train = vct.fit_transform(x_train)
    logger.info(f"[{name}] Vectorizing outputs...")
    y_train = le.fit_transform(y_train)

    logger.info(f"[{name}] Data shapes:")
    logger.info(f"[{name}] x_train: {x_train.shape}")
    logger.info(f"[{name}] y_train: {y_train.shape}")

    model = LinearSVC(random_state=0)
    model.fit(x_train, y_train)

    return SKLearnProblem(name, le, model, vct)


def map_single_multi_no_license_to_single_problem(x_train_multi, x_train_no_license, x_train_single, y_train_multi,
                                                  y_train_no_license, y_train_single):
    is_multilabel = lambda y: ClassificationResult.MULTI.value if len(y) > 1 else ClassificationResult.SINGLE.value
    x_train = x_train_single + x_train_multi + list(x_train_no_license)
    y_train = [is_multilabel(y) for y in y_train_single + y_train_multi] + list(y_train_no_license)
    return x_train, y_train


def load_data(max_samples, **query):
    x_train = []
    y_train = []
    with ProcessPoolExecutor(max_workers=n_cores) as executor:
        futures = [executor.submit(load_data_for_one_license, training_license, max_samples, **query) for
                   training_license in
                   training_licenses]

        for future in as_completed(futures):
            x_train_n, y_train_n = future.result()
            x_train += x_train_n
            y_train += y_train_n
            # memory cleanup
            future._result = None
            del x_train_n
            del y_train_n
    return x_train, y_train


def load_no_license_data(max_samples, **query):
    logger.info(f"Loading {max_samples} no license data from database ...")
    x_train = []
    y_train = []
    batch_size = 10_000
    collection_size = min(db.get_collection_size(Documents.Conclusion, **query), max_samples)
    batch_size = min(batch_size, collection_size // cpu_count())
    if batch_size:
        skips = range(0, collection_size, batch_size)
        db.reset_connection_references(Documents.Conclusion)

        with ProcessPoolExecutor(max_workers=n_cores) as executor:
            futures = [executor.submit(load_no_license_data_for_batch, skip_n, batch_size, **query)
                       for skip_n in skips]

            for future in as_completed(futures):
                x_train_n, y_train_n = future.result()
                x_train += x_train_n
                y_train += y_train_n
                # memory cleanup
                future._result = None
                del x_train_n
                del y_train_n
    else:
        x_train, y_train = load_no_license_data_for_batch(0, collection_size, ** query)
    return x_train, y_train


def load_data_for_one_license(training_license, max_samples, **query):
    with db.connect():
        query['mapped_licenses'] = training_license
        docs = Documents.Conclusion.objects(**query).only('license_related_words',
                                                          'licenses',
                                                          'mapped_licenses').limit(max_samples)

    training_tuples = [(doc.license_related_words, doc.mapped_licenses) for doc in docs if
                       doc.mapped_licenses and doc.license_related_words]

    # theoretically there must be at least 2 samples per license in order to run classification algorithms
    # practically, and also because of robustness of algorithm we set the low limit to >=10
    if training_tuples and len(training_tuples) >= 10:
        x_train_n, y_train_n = zip(*training_tuples)
    else:
        x_train_n, y_train_n = [], []

    logger.info(f"Train documents: {docs._mongo_query} count: {len(x_train_n)}")
    return x_train_n, y_train_n


def load_no_license_data_for_batch(skip_n, batch_size, **query):
    with db.connect():
        docs = Documents.Conclusion.objects(**query).skip(skip_n).limit(batch_size).only('no_license_related_words')

    training_tuples = [(doc.no_license_related_words, ClassificationResult.NO_LICENSE.value) for doc in docs if
                       doc.no_license_related_words]
    if training_tuples:
        x_train_n, y_train_n = zip(*training_tuples)
    else:
        x_train_n, y_train_n = [], []

    logger.info(f"Train documents: {docs._mongo_query} count: {len(x_train_n)}")
    return x_train_n, y_train_n


def tokens_are_elements_of_list(x):
    return x


def get_new_vectorizer():
    return TfidfVectorizer(sublinear_tf=True,
                           min_df=1,
                           norm='l2',
                           ngram_range=(1, 3),
                           analyzer='word',
                           tokenizer=tokens_are_elements_of_list,
                           preprocessor=tokens_are_elements_of_list,
                           max_features=10_000,
                           token_pattern=None)


def generate_license_text_lookup(problems):
    with db.connect():
        single = Documents.License.objects(tags=Tag.SINGLE_MAPPED_LICENSE.value, mapped_licenses__size=1)

    single_texts = {doc.mapped_licenses[0]: doc.text for doc in single if doc.mapped_licenses and doc.text}
    known_licenses = set([a for b in [x.encoder.classes_ for x in problems] for a in b])

    license_text_lookup = {}
    for license in known_licenses:
        if license in single_texts:
            license_text_lookup[license] = single_texts[license]
    return license_text_lookup


def run_and_save_problem(name, data):
    problem = data['function'](data['x'], data['y'], name)
    problem.save(data_loader.path / name)
    return problem


def train_problems_on_data(pipeline, data, train_in_parallel):
    trained_problems = []
    if train_in_parallel:
        futures = []
        # max workers restricted to 2, because classifying requires lot of RAM resource
        with ProcessPoolExecutor(max_workers=2) as executor:
            for problem_name, problem_data in data.items():
                futures.append(executor.submit(run_and_save_problem, problem_name, problem_data))

            for future in as_completed(futures):
                trained_problems.append(future.result())
    else:
        for problem_name, problem_data in data.items():
            problem_result = run_and_save_problem(problem_name, problem_data)
            trained_problems.append(problem_result)

    pipeline.license_text_lookup = generate_license_text_lookup(trained_problems)
    pipeline.save(trained_problems)


def train_sk_pipeline(pipeline, max_samples, train_in_parallel=False, exclude_data_for_benchmark=True):
    if exclude_data_for_benchmark:
        excluded_tags = [Tag.TEST.value]
    else:
        excluded_tags = []

    logger.info(
        f'Training on max {max_samples} samples for {len(training_licenses)} unique licenses\n{training_licenses}')

    x_single_label, y_single_label = load_data(max_samples=max_samples,
                                               tags__all=[Tag.SINGLE_MAPPED_LICENSE.value],
                                               tags__nin=excluded_tags)

    x_multi_label, y_multi_label = load_data(max_samples=max_samples,
                                             tags__all=[Tag.MULTIPLE_MAPPED_LICENSE.value],
                                             tags__nin=excluded_tags)

    max_samples_for_dual_problem = min(len(x_single_label), len(x_multi_label)) // 3
    x_no_license, y_no_license = load_no_license_data(max_samples=max_samples_for_dual_problem,
                                                      tags=Tag.NO_LRW.value)

    x_dual_problem, y_dual_problem = map_single_multi_no_license_to_single_problem(
                                                                        x_multi_label[:max_samples_for_dual_problem],
                                                                        x_no_license,
                                                                        x_single_label[:max_samples_for_dual_problem],
                                                                        y_multi_label[:max_samples_for_dual_problem],
                                                                        y_no_license,
                                                                        y_single_label[:max_samples_for_dual_problem])

    data = {
        "SP": {
            'function': single_label,
            'x': x_single_label,
            'y': y_single_label
        },
        "MP": {
            'function': multi_label,
            'x': x_multi_label,
            'y': y_multi_label
        },
        "DP": {
            'function': single_label,
            'x': x_dual_problem,
            'y': y_dual_problem
        },
    }

    train_problems_on_data(pipeline, data, train_in_parallel)


if __name__ == '__main__':
    logger = root_logger('train_sk_pipeline', logging.INFO)
    load_dotenv(find_dotenv())

    scenario_dir = Path(get_train_dir() / f'sklearn_{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")}')
    scenario_dir.mkdir(parents=True, exist_ok=True)
    add_file_handler_to_logger(logger, scenario_dir, 'train_sk_pipeline')

    try:
        db = MongoDB()  # credentials for MongoDB can be set up here
        n_cores = cpu_count()  # number of processors that shall be used for loading data from MongoDB
        max_samples = 10_000  # max number of samples per license, used for single and multi label problem, value
        min_samples = 1_000  # min number of samples per license, decides if the license will be taken to training, internally limited to 10

        collection_analysis = CollectionAnalysis.load_object(get_db_analysis_dir() / 'Conclusion.pkl')

        training_licenses = collection_analysis.get_mapped_licenses_with_min_samples(min_samples)

        data_loader = DataLoaderCustom(scenario_dir)
        pipeline = SKLearnPipeline(ConfigParser(), data_loader)

        train_sk_pipeline(pipeline,
                          max_samples=max_samples,
                          train_in_parallel=True,
                          exclude_data_for_benchmark=True)

    except Exception as e:
        logger.exception(e)
