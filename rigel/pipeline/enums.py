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
from enum import Enum


class ClassificationResult(Enum):
    SINGLE = "single"
    MULTI = "multi"
    LICENSE = "license"  # means rigel predicts there is a license
    NO_LICENSE = "no license"  # means rigel is sure there is no license in the document
    UNCLASSIFIED = "unclassified license"  # means rigel predicts there is a license but it can not say which

    def __str__(self):
        return str(self.value)


class MimeType:
    C = r'text/x-c'
    C_PLUS_PLUS = r'text/x-c++'
    JAVA = r'text/x-c'
    HTML = r'text/html'
    XML = r'text/xml'
    SGML = r'text/html'
    PYTHON = r'text/x-python'
    SHELL = r'text/x-shellscript'
    PHP = r'text/x-php'
    UNKNOWN = 'unknown filetype'


class MagicToMimeType:
    MAPPING = {
        "C source": MimeType.C,
        "C++ source": MimeType.C_PLUS_PLUS,
        "HTML document": MimeType.HTML,
        "XML 1.0 document": MimeType.XML,
        "SGML document": MimeType.SGML,
        "Python script": MimeType.PYTHON,
        "POSIX shell script": MimeType.SHELL,
        "PHP document": MimeType.PHP
    }


class Column(Enum):
    """
    Columns to be used for a FOSSology .csv dump
    """
    PATH = 0
    CONCLUSION_RESULT = 1
    SCANNER_RESULT = 2
    SOURCE = 3


class Source(Enum):
    CONCLUSION = 'CONCLUSION'
    BULK = 'BULK'
    BULK_REMOVE = 'BULK_REMOVE'
    LICENSE = 'LICENSE'
    LICENSE_INDIRECT = 'LICENSE_INDIRECT'
    NINKA = 'ninka'
    NOMOS = 'nomos'
    MONK = 'monk'

    def __str__(self):
        return str(self.value)


class Tag(Enum):
    SINGLE_LICENSE = 'SINGLE_LICENSE'
    MULTIPLE_LICENSE = 'MULTIPLE_LICENSE'
    SINGLE_MAPPED_LICENSE = 'SINGLE_MAPPED_LICENSE'
    MULTIPLE_MAPPED_LICENSE = 'MULTIPLE_MAPPED_LICENSE'
    LRW = 'LRW'
    NO_LRW = 'NO_LRW'
    TEST = 'TEST'

    def __str__(self):
        return str(self.value)


class Mapping(Enum):
    NO_MAPPED_LICENSE = 'NO_MAPPED_LICENSE'
    MULTI_LICENSE = 'MULTI_LICENSE'

    def __str__(self):
        return str(self.value)


SCANNERS = ('ninka', 'nomos', 'monk')
SOURCES = tuple(map(lambda c: c.value, Source))
PIPELINE_CONFIG_FILENAME = 'conf.ini'

if __name__ == '__main__':
    pass
