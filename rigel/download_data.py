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
Call this script after rigel is installed because it loads the necessary depencies for Spacy and tries to download the
default model
"""

import urllib
from pathlib import Path

import patoolib
import requests

from rigel import utils as utils
from rigel.pipeline.enums import PIPELINE_CONFIG_FILENAME


def download_archive(url: str, download_data_to_dir: Path) -> Path:
    """
    Downloads archive from the given url and saves it under download_data_dir
    :param url:
    :param download_data_to_dir:
    :return: archive_file: path to downloaded archive
    """
    archive_name = Path(urllib.request.url2pathname(url)).name
    archive_file = download_data_to_dir / archive_name

    r = requests.get(url)

    if r.status_code == 200 and r.request:
        download_url = r.request.url
        print(f'Redirected to {download_url}')

        r = requests.get(download_url, headers={'Accept': 'application/octet-stream'})

        if r.status_code != 200:
            print('URL not valid or returning error, exiting!')

        with open(archive_file, 'wb') as f:
            f.write(r.content)

        return archive_file

    if r.status_code != 200:
        print('URL not valid or returning error, exiting!')
        return False


def download_nltk_data():
    print('Downloading data for PreprocessorNltk ...')
    try:
        from nltk import download
        download('stopwords')
        download('punkt')
    except ImportError:
        print('Could not import data for PreprocessorNltk. Check your internet connection')
        return
    print('Success')


def download_spacy_data():
    print('Downloading data for PreprocessorSpacy ...')
    try:
        from spacy.cli.download import download
        download('en')
    except ImportError:
        print('Could not import data for PreprocessorSpacy. Check your internet connection and try again')


def download_default_model():
    """
    Tries to download the default model corresponding version of the installed rigel package.
    """
    model_dir = utils.get_default_model_dir()
    if not Path(model_dir / PIPELINE_CONFIG_FILENAME).exists():

        version = utils.get_module_version()
        url = f'https://github.com/mcjaeger/rigel/releases/download/v{version}/default_model_{version}.zip'
        print(f'Downloading default model from: {url}')

        archive_file = download_archive(url, model_dir)
        if archive_file:
            patoolib.extract_archive(str(archive_file), outdir=str(model_dir))
            print('Success')
        else:
            print(
                f'WARNING!'
                f' Could not download the default model, try to download manually from: {url}'
                f' and extract the package into: {model_dir}/')

    else:
        print(f'Downloading default model would overwrite the existing model in: {model_dir}.\n'
              f'Rename or move the default_model directory and try again.')


def download():
    download_spacy_data()
    download_nltk_data()
    download_default_model()


if __name__ == '__main__':
    download()
