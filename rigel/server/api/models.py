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

import logging

from flask_restful import fields
from flask_restful_swagger import swagger

logger = logging.getLogger("rigel-server")


@swagger.model
class PredictResult(object):
    """The result of a call to /model"""
    resource_fields = {
        'licenses': fields.List(fields.String)
    }

    def __init__(self, licenses: list):
        self.licenses = licenses
        logger.debug(f'Created response: {self.__dict__}')


@swagger.model
class ModelResult(object):
    """The result of a call to /model"""
    resource_fields = {
        'modelInfo': fields.Raw()
    }

    def __init__(self, model_info):
        self.modelInfo = model_info
        logger.debug(f'Created response: {self.__dict__}')


@swagger.model
class LicenseResult(object):
    """The result of a call to /model"""
    resource_fields = {
        'licenseName': fields.String(),
        'licenseText': fields.String(),
    }

    def __init__(self, license_name, license_text):
        self.licenseName = license_name
        self.licenseText = license_text
        logger.debug(f'Created response: {self.__dict__}')
