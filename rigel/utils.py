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
Collection of utility functions (logging, directory handling, ...)
"""

import glob
import logging
import os
import subprocess
from json import dumps
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Union, List

import magic
from pkg_resources import get_distribution

from rigel.pipeline.enums import *
from rigel.pipeline.preprocessor.comment_extractor import MimeType

logger = logging.getLogger(__name__)
LOG_FORMATER = logging.Formatter(
    "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")


def get_module_version(module: str = 'rigel'):
    return get_distribution(module).version


def setup_logger(logger: logging.Logger, quiet_mode: bool):
    """
    Convenience function to setup the logging behavior. Adds file handler to get log into respective file.::
    :param quiet_mode: True if the console output should be suppressed.
    """
    # remove console handler
    if quiet_mode:
        logger.handlers.pop(0)
    # add file handler
    add_file_handler_for_logger(logger)


def add_file_handler_for_logger(logger: logging.Logger):
    """
    Adds a new file handler to logger
    """
    fh = TimedRotatingFileHandler(get_logs_dir() / str(logger.name + '.log'),
                                  when="midnight",
                                  interval=1,
                                  backupCount=10)

    fh.setLevel(logger.level)
    fh.setFormatter(LOG_FORMATER)
    logger.addHandler(fh)


def get_rigel_dir() -> Path:
    """
    This function is needed for the Apache server. It returns the directory of the rigel folder.
    :return:
    """
    # needed for compatiblity with mod_wsgi virtual host, see rigel/server/rigelapp.wsgi
    try:
        rigel_dir = Path(os.environ['RIGEL_DIR'])
    except KeyError:
        rigel_dir = Path.home() / "rigel"
    rigel_dir.mkdir(parents=True, exist_ok=True)
    return rigel_dir


def get_data_dir() -> Path:
    return get_rigel_dir() / "data"


def get_default_model_dir() -> Path:
    """
    Creates the default model if it doesn't exist
    """
    default_model_dir = Path(get_rigel_dir() / 'models' / 'default_model')
    default_model_dir.mkdir(parents=True, exist_ok=True)
    return default_model_dir


def get_logs_dir() -> Path:
    """
    Create logs dir if it doesn't exist.
    """
    logs_dir = Path(get_rigel_dir() / 'logs')
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True)
    return logs_dir


def get_file_content(input_filepath: Path) -> Union[str, None]:
    """
    Returns the contents of a file as a raw string (with newlines etc ...)
    It the file could not be decoded (e.g. image) returns None.::
    :param input_filepath:
    :return: content: None if the file could not be decoded or was not found
    """
    content = None

    try:
        # we take latin-1 encoding to be able to read metadata from jpegs, pdfs etc
        with open(input_filepath, mode='r', encoding='latin-1') as f:
            content = f.read()
    except UnicodeDecodeError:
        logger.warning(f'Could not read the file contents of: {input_filepath}')

    return content


def get_file_list(input_path: Path, search_pattern: str = '**') -> List[Path]:
    """
    Returns a list of files found recursively under given input_path.
    If the input_path is a file it returns itself as a single member list.::
    :param input_path:
    :param search_pattern:
    :return: file_list:
    """
    if Path(input_path).is_dir():
        file_list = glob.glob(str(input_path) + '**/' + search_pattern, recursive=True)
        file_list = [Path(file) for file in file_list if Path(file).is_file()]
    else:
        file_list = [Path(input_path)]

    return file_list


def get_file_type_with_unix(file_path: Path) -> str:
    """
    Get a textual description of a file's type (e.g. that it is a Python script, C Source etc). This is done by
    calling the unix "file" command. If it is not available (e.g. on Windows), "unknown filetype" will be returned
    :param file_path: The file to be analyzed
    :return: The file type, if "file" is available on the system, "unknown filetype" otherwise
    """
    file_path = file_path.resolve()
    if file_path.exists():
        try:
            p = subprocess.Popen(['file', '-b', '--mime-type', str(file_path)], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, errors = p.communicate()
            return output.decode('utf-8')
        except FileNotFoundError:
            logger.warning(f'unix file command not found in PATH, returning "{MimeType.UNKNOWN}"')
            return MimeType.UNKNOWN
    return MimeType.UNKNOWN


def get_file_type_from_path(file_path: Path) -> str:
    """
    Get a textual description of a file's type (e.g. that it is a Python script, C Source etc) from filepath.
    This is done by calling the python-magic module. If it is not available (e.g. on Windows), "unknown filetype" will be returned
    :param file_path:
    :return: The file type, if "magic.dll" is available on the system, "unknown filetype" otherwise
    """
    stream = get_file_content(file_path)
    return get_file_type_from_stream(stream)


def get_file_type_from_stream(stream: str) -> str:
    """
    Get a textual description of a file's type (e.g. that it is a Python script, C Source etc) from bytestream.
    This is done by calling the python-magic module. If it is not available (e.g. on Windows), "unknown filetype" will be returned
    :param stream: bytestream
    :return: The file type, if "magic.dll" is available on the system, "unknown filetype" otherwise
    """
    if stream:
        try:
            raw_value = magic.from_buffer(stream, mime=False).split(',', maxsplit=1)[0]
            return MagicToMimeType.MAPPING.get(raw_value, MimeType.UNKNOWN)
        except ImportError as e:
            logger.warning(f'{e}')
            return MimeType.UNKNOWN
    return MimeType.UNKNOWN


def get_file_safe_license_name(license_name: str) -> str:
    """
    Converts the license name to comply with valid filenaming
    :param license_name:
    :return:
    """
    keepcharacters = ('_')
    license_name = license_name.replace("-", "_")
    license_name = license_name.replace(".", "_")
    return "".join(c for c in license_name if c.isalnum() or c in keepcharacters).rstrip()


def to_json(my_object, pretty=False):
    """
    Returns object and subobjects as serialized JSON string
    :param my_object:
    :return:
    """
    if pretty:
        return dumps(my_object, indent=4, default=lambda x: x.__dict__)
    else:
        return dumps(my_object, default=lambda x: x.__dict__)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
