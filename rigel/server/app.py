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
The module with the rigel server app definition and routing.
"""

from flask import Flask
from flask_restful import Api
from flask_restful_swagger import swagger

from rigel import utils as utils
from rigel.server.api.endpoints import PredictEndpoint, ModelEndpoint, LicenseEndpoint

API_VERSION_NUMBER = utils.get_module_version()


class RigelFlaskApp(object):

    def __init__(self):
        self.app = Flask(__name__)

        custom_errors = {
            'JsonInvalidError': {
                'status': 500,
                'message': 'JSON format not valid'
            },
            'JsonRequiredError': {
                'status': 400,
                'message': 'JSON input required'
            },
            'PipelineError': {
                'status': 500,
                'message': 'Pipeline processing error'
            },
        }

        self.api = swagger.docs(Api(self.app, errors=custom_errors),
                                api_spec_url='/help',
                                description='Auto generated API docs for rigel-server',
                                apiVersion=API_VERSION_NUMBER)

        self.api.add_resource(PredictEndpoint, '/predict',
                              endpoint='predict',
                              strict_slashes=False)
        self.api.add_resource(ModelEndpoint, '/model',
                              endpoint='model',
                              strict_slashes=False)
        self.api.add_resource(LicenseEndpoint, '/license',
                              endpoint='license',
                              strict_slashes=False)

    def run(self, *args, **kwargs):
        self.app.config['PROPAGATE_EXCEPTIONS'] = False
        self.app.run(*args, **kwargs)


if __name__ == '__main__':
    pass
