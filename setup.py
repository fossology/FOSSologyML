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

from setuptools import setup, find_packages

__VERSION__ = "0.0.0a0"
__NAME__ = 'rigel'

with open('README.rst') as readme_file:
    README = readme_file.read()

setup(
    name=__NAME__,
    version=__VERSION__,
    python_requires='>=3.6',
    author='Siemens AG',
    author_email='TODO',
    description='Open Source License Classifier',
    long_description=README,
    license='GPL-2.0',
    platforms=['Linux'],
    url='https://github.com/mcjaeger/rigel',
    download_url='git+https://github.com/mcjaeger/rigel.git',
    packages=find_packages(),
    include_package_data=True,
    setup_requires=[
        'pytest-runner'
    ],
    install_requires=[
        'beautifulsoup4==4.7.1',
        'click==7.0',
        'click-log==0.3.2',
        'Flask==1.0.2',
        'Flask-RESTful==0.3.7',
        'flask-restful-swagger==0.20.1',
        'h5py==2.9.0',
        'numpy==1.16.2',
        'python-magic==0.4.15',
        'scipy==1.2.1',
        'scikit-learn==0.20.3',
        'scikit-multilearn==0.2.0',
        'spacy==2.1.0',
        'Sphinx==1.8.0',
        'patool==1.12',
        'lxml==4.2.4',
        'Nirjas==0.0.5',
    ],
    test_suite='test',
    tests_require=[
        'pytest',
        'nltk',
    ],
    entry_points={
        'console_scripts': [
            'rigel-cli=rigel.cli.cli:main',
            'rigel-server=rigel.server.runserver:run_app',
            'rigel-download-data=rigel.download_data:download'
        ]
    }
)
