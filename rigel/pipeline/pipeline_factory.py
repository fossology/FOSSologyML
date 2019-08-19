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
Creates the Pipeline and serves as extendable endpoint in case different pipeline-types are available in the future
"""
import logging
from configparser import ConfigParser, NoSectionError, NoOptionError
from pathlib import Path

from rigel import utils as utils
from rigel.pipeline.dataloader.data_loader import DataLoaderCustom
from rigel.pipeline.enums import PIPELINE_CONFIG_FILENAME
from rigel.pipeline.sk_pipeline import SKLearnPipeline
from rigel.pipeline.sk_pipeline_special_cases import SpecialSKLearnPipeline

logger = logging.getLogger(__name__)
module_version = utils.get_module_version()


class PipelineFactory:

    def __init__(self, config_path: Path):
        self.config = ConfigParser()
        self.config_file = config_path / PIPELINE_CONFIG_FILENAME
        self.config.read(str(self.config_file))
        self.dataloader = DataLoaderCustom(config_path)
        self._validate_version()

    def _validate_version(self):
        try:
            config_version = self.config.get('rigel', 'version')
        except NoSectionError as e:
            raise PipelineFactoryException(
                f'Error while initializing pipeline, error or missing model configuration file {self.config_file}: {e}') from e
        except NoOptionError:
            logger.warning(
                f'No model version definition in: {self.config_file}. Proceeding without validation might cause unexpected errors!')
            config_version = module_version

        if config_version != module_version:
            raise PipelineFactoryException(
                f'Pipeline version incompatibility. Model version: {config_version} differs from rigel module version: {module_version}')

    def build_model(self) -> 'SKLearnPipeline':
        try:
            pipeline = self.config.get('rigel', 'pipeline')
        except NoOptionError as e:
            raise PipelineFactoryException(
                f'Error while initializing pipeline, error in configuration file {self.config_file}: {e}') from e

        if pipeline == SKLearnPipeline.pipeline_name:
            return SKLearnPipeline(self.config, self.dataloader).load()
        elif pipeline == SpecialSKLearnPipeline.pipeline_name:
            return SpecialSKLearnPipeline(self.config, self.dataloader).load()
        elif pipeline == 'pytorch':
            return None
        else:
            raise PipelineFactoryException(
                f'Unknown pipeline definition: "{pipeline}" in: {self.config_file}')


class PipelineFactoryException(Exception):
    """Raised when problems occured during pipeline initialization"""

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


if __name__ == '__main__':
    pass
