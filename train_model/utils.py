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
Collection of utility functions used only for training the model
"""

import csv
import datetime
import logging
import logging.handlers
from pathlib import Path

logger = logging.getLogger(__name__)


def root_logger(log_name: str = 'default', verbosity=logging.INFO):
    """
    Get a logger for stdout and file logging
    :param log_name: The tag to be prepended for any logged messages
    :param verbosity: log level, see :mod:`logging`
    :return: A logger object. See :func:`logging.getLogger`
    """

    log_level = logging.getLevelName(verbosity)

    # create root logger
    logger = logging.getLogger('')
    logger.setLevel(log_level)

    if not len(logger.handlers):
        # create console handler and set log level
        ch = logging.StreamHandler()
        ch.setLevel(log_level)

        # create file handler and set log level
        fh = logging.FileHandler(get_logs_dir() / str(log_name + '.log'))
        fh.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter(
            "%(asctime)s - " + log_name + "[%(name)s] - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

        # add formatter to ch and fh
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        # add ch and fh to logger
        logger.addHandler(ch)
        logger.addHandler(fh)

        insert_log_separator()

    return logger


def add_file_handler_to_logger(logger, log_dir, file_name):
    formatter = logging.Formatter(
        "%(asctime)s - " + file_name + "[%(name)s] - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    fh_scenario = logging.FileHandler(log_dir / str(file_name + '.log'))
    fh_scenario.setLevel(logging.DEBUG)
    fh_scenario.setFormatter(formatter)
    logger.addHandler(fh_scenario)


def insert_log_separator():
    logger.info('*')
    logger.info('*')
    logger.info('*')


def get_train_dir():
    return Path(__file__).resolve().parents[0]


def get_data_dir():
    """
    Create data dir if it doesn't exist.
    """
    data_dir = get_train_dir() / 'data'
    if not data_dir.exists():
        data_dir.mkdir(exist_ok=True)
    return data_dir


def get_db_analysis_dir():
    """
    Create database_analysis dir if it doesn't exist.
    """
    db_analysis_dir = get_train_dir() / 'database_analysis'
    if not db_analysis_dir.exists():
        db_analysis_dir.mkdir(exist_ok=True)
    return db_analysis_dir


def get_logs_dir():
    """
    Create logs dir if it doesn't exist.
    """
    logs_dir = get_train_dir() / 'logs' / datetime.date.today().strftime("%Y_%m_%d")
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def log_progress(current, total, comment='', num_log_outputs=10):
    """
    Logging utility that prints progress percentage for a given absolute progress. Can be called as often as desired,
    will handle verbosity limitation automatically depending on the passed log_interval
    :param current: The current absolute progress
    :param total: The total to be reached for 100%
    :param comment: A tag to be prepended
    :param num_log_outputs: Only print progress num_log_outputs times
    """
    num_log_outputs = max(total // num_log_outputs, 1)
    progress = round(current / total * 100)
    if current % num_log_outputs == 0:
        logger.info('%s Completed %d %% (%d / %d)', comment, progress, current, total)


def write_license_mapping_file(licenses: list):
    """
    Generates a template for license mapping file in format
    <old_license>;<here you can define new mapping1>; <here you can define new mapping2> ...
    :param licenses: list of licenses
    """
    output_path = get_train_dir() / LICENSE_MAPPING_FILENAME

    with open(output_path, "w") as f:
        writer = csv.writer(f, delimiter=';')
        for license in licenses:
            writer.writerow((license, ""))

    logger.info(f'License mapping file generated in :{output_path}')


def ignore_exception(ignore_exception=Exception, default=None):
    """ Decorator for ignoring exception from a function
    e.g.   @ignore_exception(DivideByZero)
    e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
    """

    def dec(func):
        def _dec(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ignore_exception:
                return default

        return _dec

    return dec


"""
Parse a string value to an int but suppress any exception that may occur and return None instead.
"""
sint = ignore_exception(ValueError)(int)

LICENSE_MAPPING_FILENAME = 'license_mapping.csv'

if __name__ == '__main__':
    pass
