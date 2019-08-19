#!/usr/bin/env python
# -*- encoding: utf-8 -*-
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
Module with prediction logic
"""

import logging
from pathlib import Path
from typing import List

from requests import post, exceptions

from rigel import utils as utils
from rigel.pipeline.sk_pipeline import SKLearnPipeline

logger = logging.getLogger("rigel-cli")


class PredictionLogic:

    def __init__(self):
        pass

    def predict(self, file: Path) -> 'PredictionResult':
        raise NotImplementedError


class LocalPredictor(PredictionLogic):
    """
    Loads a local prediction pipeline
    """

    def __init__(self, pipeline: 'SKLearnPipeline'):
        super().__init__()
        try:
            self.pipeline = pipeline
        except Exception as e:
            raise PredictionLogicException(
                'Error while initializing prediction Logic, make sure the model directory is in correct format') from e

    def predict(self, file: Path) -> 'PredictionResult':
        """
        :param file: Path to the file that needs to be scanned
        :return: license prediction
        """
        predicted_licenses = self.pipeline.predict(utils.get_file_content(file), utils.get_file_type_from_path(file))
        prediction_result = PredictionResult(file, predicted_licenses)

        logger.debug(f'PredictLocal license(s): {utils.to_json(prediction_result, pretty=True)}')

        return prediction_result


class ServerPredictor(PredictionLogic):
    """
    Serves as a client and sends a prediction to the server and parses the response
    """

    def __init__(self, api_endpoint: str):
        super().__init__()
        self.api_endpoint = api_endpoint

    def predict(self, file: Path) -> 'PredictionResult':
        """
        Sends to content of the file to the local server and obtains the prediction
        :param file: Path to the file that needs to be scanned
        :return:  license prediction
        """
        request_payload = {
            'text': utils.get_file_content(file),
            'fileType': utils.get_file_type_from_path(file)
        }

        try:
            response = post(self.api_endpoint, json=request_payload)
        except exceptions.ConnectionError as e:
            raise PredictionLogicException(f'Could not connect to {self.api_endpoint}') from e
        if response.status_code != 200:
            raise PredictionLogicException(
                f"Invalid answer from {response.url}: {response.status_code} - {response.reason} - {response.text}")
        prediction_result = PredictionResult(file, response.json()['licenses'])

        logger.debug(f'PredictOnServer license(s): {utils.to_json(prediction_result, pretty=True)}')

        return prediction_result


class PredictionLogicException(Exception):
    """Raised when problems occurred during prediction"""
    pass


class PredictionResult(object):
    """
    Struct to encapsulate prediction results for one file
    """

    def __init__(self, filename: Path, licenses: List[str]):
        self.filename = str(filename)
        self.licenses = licenses


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
