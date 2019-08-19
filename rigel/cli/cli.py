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
Main class handling CLI interaction
"""
import datetime
import logging
import warnings

import click
import click_log
from pathlib import Path
from rigel import utils as utils
from rigel.cli.prediction_logic import ServerPredictor, LocalPredictor
from rigel.pipeline.pipeline_factory import PipelineFactory

# this is workaround to have clean stdout/stderr, the problem is in sklearn preprocessor implementation itself
warnings.filterwarnings("ignore", category=DeprecationWarning)

version = utils.get_module_version()
logger = logging.getLogger("rigel-cli")
click_log.basic_config(logger)

context_settings = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=context_settings)
@click.version_option(version=version)
@click_log.simple_verbosity_option(logger)
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--model_path', '-m', type=click.Path(exists=True), help='Input path to directory with model. Default model located under your $HOME/rigel/models/')
@click.option('--quiet', '-q', is_flag=True, help='Suppress logging to console')
def main(input_path: Path, model_path: Path, quiet: bool):
    """
    Open Source License Classifier CLI

    This tool will classify file in INPUT_PATH based on it's open source license compliance.
    If INPUT_PATH is a directory all underlying files will be classified recursively.

    """
    try:
        utils.setup_logger(logger, quiet)
        logger.info(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} *** START rigel-cli {version} ***')

        model_path = Path(model_path).resolve() if model_path else utils.get_default_model_dir()
        prediction_logic = LocalPredictor(PipelineFactory(model_path).build_model()) # to predict local
        # prediction_logic = ServerPredictor(api_endpoint='http://127.0.0.1:5000/predict') # to predict on server
        files = utils.get_file_list(input_path)

        result = [prediction_logic.predict(file) for file in files]

        click.secho(utils.to_json(result), fg='green')

    except Exception as e:
        logger.error(e, exc_info=True)
        raise click.ClickException(
            f'{e}. \nSee stacktrace in: {utils.get_logs_dir()}') from e

    finally:
        logger.info(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} *** END rigel-cli {version} ***')


if __name__ == '__main__':
    main()
