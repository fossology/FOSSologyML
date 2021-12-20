# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2021, Siemens AG
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
The file takes file path as address and extracts multiline comments which may contain some license
information. 
"""

import json
import os
import re
import string
import tempfile

from nirjas import extract as commentExtract, LanguageMapper

args = None

def licenseComment(data):
  match_list = ['source', 'free', 'under','use',  'copyright', 'grant', 'software', 'license','licence', 'agreement', 'distribute', 'redistribution', 'liability', 'rights', 'reserved', 'general', 'public', 'modify', 'modified', 'modification', 'permission','permitted' 'granted', 'distributed', 'notice', 'distribution', 'terms', 'freely', 'licensed', 'merchantibility','redistributed', 'see', 'read', '(c)', 'copying', 'legal', 'licensing', 'spdx']

  comment = ""
  tempCount = 0
  if "multi_line_comment" in data:
    for id, item in enumerate(data["multi_line_comment"]):
      count = 0
      if 'spdx-license-identifier' in item['comment'].lower():
        return item['comment']

      for i in match_list:
        if i in item['comment'].lower():
          count+=1

      if count > tempCount:
        tempCount = count
        comment = comment + " " + item['comment']

  if "cont_single_line_comment" in data:
    for id, item in enumerate(data["cont_single_line_comment"]):
      count = 0
      if 'spdx-license-identifier' in item['comment'].lower():
        return item['comment']

      for i in match_list:
        if i in item['comment'].lower():
          count+=1

      if count > tempCount:
        tempCount = count
        comment = comment + " " + item['comment']

  if "single_line_comment" in data:
    for id, item in enumerate(data["single_line_comment"]):
      count = 0
      if 'spdx-license-identifier' in item['comment'].lower():
        return item['comment']

      for i in match_list:
        if i in item['comment'].lower():
          count+=1

      if count > tempCount:
        tempCount = count
        comment = comment + " " + item['comment']

  return comment


def extract(inputFile):
    '''
    Extract comments from given input file and return a temp file stored in OS.
    This reads all comments from the different files types.
    :param inputFile: Location of Input file from which comments needs to be extracted
    :return: Temp file path from the OS
    '''

    supportedFileExtensions = list(LanguageMapper.LANG_MAP.keys())

    fileType = os.path.splitext(inputFile)[1]

    # if the file extension is supported
    if fileType in supportedFileExtensions:
        data_file = commentExtract(inputFile)
        data = json.loads(data_file)
        data1 = licenseComment(data)
        return data1
    else:
        # if file extension is not supported
        with open(inputFile) as inFile:
            lines = inFile.read().split('\n')
        return lines