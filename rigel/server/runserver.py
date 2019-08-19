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

import datetime
import logging
import warnings

import click
import click_log

from pathlib import Path

from rigel import utils as utils
from rigel.server.app import RigelFlaskApp

# this is workaround to have clean stdout/stderr, the problem is in sklearn preprocessor implementation itself
warnings.filterwarnings("ignore", category=DeprecationWarning)

version = utils.get_module_version()
logger = logging.getLogger("rigel-server")
click_log.basic_config(logger)


@click.command()
@click.version_option(version=version)
@click_log.simple_verbosity_option(logger)
@click.option('--host', '-h', default=None, help='Run server on host')
@click.option('--port', '-p', default=None, help='Run server on port')
@click.option('--debug', '-d', is_flag=True, help='Run in DEBUG mode')
def run_app(host, port, debug):
    utils.add_file_handler_for_logger(logger)
    logger.info(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                f'*** START rigel-server {version} ***')

    app = RigelFlaskApp()
    app.run(host, port, debug)

    logger.info(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                f'*** END rigel-server {version} ***')


def return_app_object():
    app = RigelFlaskApp()
    return app


if __name__ == '__main__':
    run_app()
