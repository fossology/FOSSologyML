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
Handles the entire prediction logic. A Pipeline is made up of multiple problems which each predict one step in the
entire process e.g. if a file is single or multi license etc. . The pipeline then decides which problem should be
executed next and returns the final prediction result
"""

import logging
from pathlib import Path
from typing import List

from numpy import ndarray

from rigel import utils as utils
from rigel.pipeline.dataloader.data_loader import DataLoaderCustom
from rigel.pipeline.enums import ClassificationResult, MimeType, PIPELINE_CONFIG_FILENAME
from rigel.pipeline.preprocessor.preprocessor_spacy import PreprocessorSpacy

logger = logging.getLogger(__name__)


class PipelineException(Exception):
    """Raised when problems occur during pipeline usage"""

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class SKLearnPipeline:
    pipeline_name = 'sklearn'

    def __init__(self, config_parser, dataloader):
        self.pipeline_name = SKLearnPipeline.pipeline_name
        self.preprocessor = PreprocessorSpacy()
        self.dataloader = dataloader
        self.config_parser = config_parser
        self.config_parser.optionxform = str  # configparser transforms everything to lowercase, this line prevents that
        self.single_label_problem = None
        self.multi_label_problem = None
        self.dual_problem = None
        self.words = None
        self.license_text_lookup = {}

    def load(self):
        self.single_label_problem = self._build_problem('SP')
        self.multi_label_problem = self._build_problem('MP')
        self.dual_problem = self._build_problem('DP')
        return self

    def predict(self, text: str, file_type: str = MimeType.UNKNOWN) -> List:
        """
        2-step prediction logic:
        * The "dual problem" (DP) determines whether the text contains either one or multiple licenses
        * Then, either the "single problem" (SP) is called to determine the text's single license or the "multi problem" (MP) for the multi-license case.
        :param text: The file content to be analyzed
        :param file_type: What kind of file this is (see UNIX "file" command output)
        :return: A list of license findings for this file
        :rtype: list
        """
        self.words = self.preprocessor.process(text, file_type)
        if self.words:
            problem_type = self.dual_problem.predict(self.words)[0]
            if problem_type == ClassificationResult.MULTI.value:
                return self.multi_label_problem.predict(self.words) or [ClassificationResult.UNCLASSIFIED.value]
            elif problem_type == ClassificationResult.SINGLE.value:
                return self.single_label_problem.predict(self.words) or [ClassificationResult.UNCLASSIFIED.value]
            elif problem_type == ClassificationResult.NO_LICENSE.value:
                return [ClassificationResult.NO_LICENSE.value]
        return [ClassificationResult.UNCLASSIFIED.value]

    def _build_problem(self, problem_type):
        dataloader = DataLoaderCustom(self.dataloader.path / problem_type)
        encoder = dataloader.load(self.config_parser.get(problem_type, 'encoder'))
        classifier = dataloader.load(self.config_parser.get(problem_type, 'classifier'))
        vectorizer = dataloader.load(self.config_parser.get(problem_type, 'vectorizer'))
        vectorizer.preprocessor = lambda x: x  # needed because of our custom preprocessor
        vectorizer.tokenizer = lambda x: x
        return SKLearnProblem(problem_type, encoder, classifier, vectorizer)

    def save(self, problems=None):
        """Saves the entire pipeline.

         :param problems: optional list of problems, provide your own list of trained and pipeline compatible problems
         """

        if problems is None:
            problems = [
                self.single_label_problem,
                self.multi_label_problem,
                self.dual_problem
            ]

        if None in problems:
            raise PipelineException("Not all problems are initialized, incomplete pipeline can't be saved")

        names = list(map(lambda p: p.name, problems))
        if len(set(names)) != len(problems):
            raise PipelineException("Pipeline has multiple problems with the same name")

        self.dataloader.path.mkdir(exist_ok=True, parents=True)
        logger.info(f'Saving complete pipeline including license texts and config.ini to: {self.dataloader.path}')

        self.config_parser['rigel'] = {'version': utils.get_module_version(),
                                       'pipeline': self.pipeline_name}

        self._save_problems(problems)
        self._save_license_text_lookup()
        self._save_config()

    def _save_problems(self, problems):
        for problem in problems:
            self.config_parser[problem.name] = problem.get_config()
            problem.save(self.dataloader.path / problem.name)

    def _save_config(self):
        with open(self.dataloader.path / PIPELINE_CONFIG_FILENAME, 'w') as configfile:
            self.config_parser.write(configfile)

    def _save_license_text_lookup(self):
        Path(self.dataloader.path / "licenses").mkdir(exist_ok=True, parents=True)
        for name, text in self.license_text_lookup.items():
            license_text_path = Path(self.dataloader.path / "licenses" / utils.get_file_safe_license_name(name))
            with open(license_text_path, 'w+') as file:
                file.write(text)

    def get_license_text(self, license_name):
        try:
            license_text_path = Path(self.dataloader.path / "licenses" / utils.get_file_safe_license_name(license_name))
            with open(license_text_path, 'r') as file:
                return file.read()
        except FileNotFoundError as e:
            logger.warning(
                f'Could not load license text lookup file {e.filename}, returning "License by rigel" as a fallback.')
            return "License by rigel"


class SKLearnProblem:
    """
    Defines a single prediction step in the pipeline e.g. one classification step

    :ivar vectorizer: Vectorizer for the specific problem. Different vectorizers are needed because their training vocabulary vastly differs on the task they need to predict.
    :ivar encoder: Either label or MultilabelBinarizer encoder
    """

    def __init__(self, name, encoder, classifier, vectorizer):
        self.name = name
        self.vectorizer = vectorizer
        self.classifier = classifier
        self.encoder = encoder

    def save(self, path: Path):
        dataloader = DataLoaderCustom(path)

        encoder_name = 'encoder' + DataLoaderCustom.determine_suffix(self.encoder)
        classifier_name = 'classifier' + DataLoaderCustom.determine_suffix(self.classifier)
        vectorizer_name = 'vectorizer' + DataLoaderCustom.determine_suffix(self.vectorizer)

        dataloader.save(self.encoder, encoder_name)
        dataloader.save(self.classifier, classifier_name)
        dataloader.save(self.vectorizer, vectorizer_name)

        logger.info(f"Saved {self.name} problem to: {dataloader.path}")

    def get_config(self) -> dict:
        encoder_name = 'encoder' + DataLoaderCustom.determine_suffix(self.encoder)
        classifier_name = 'classifier' + DataLoaderCustom.determine_suffix(self.classifier)
        vectorizer_name = 'vectorizer' + DataLoaderCustom.determine_suffix(self.vectorizer)

        config = {
            'encoder': encoder_name,
            'classifier': classifier_name,
            'vectorizer': vectorizer_name
        }

        return config

    def predict(self, labels: list) -> list:
        """"
        Converts the token list into vectors and delivers the prediction

        :param labels: token list of License relevant Words
        :type labels: list of strings
        :return list of human readable predictions
        :rtype list"""
        vectorized = self.vectorizer.transform([labels])
        raw_prediction = self.classifier.predict(vectorized)
        result = self.encoder.inverse_transform(raw_prediction)
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        elif isinstance(result, ndarray):
            return result.tolist()
        else:
            return [ClassificationResult.UNCLASSIFIED]
