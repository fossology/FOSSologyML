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
from pathlib import Path

from flask import request
from flask_restful import Resource, marshal_with
from flask_restful_swagger import swagger

from rigel.pipeline.pipeline_factory import PipelineFactory
from rigel.utils import get_default_model_dir
from .errors import JsonInvalidError, JsonRequiredError, PipelineError
from .models import PredictResult, ModelResult, LicenseResult

logger = logging.getLogger("rigel-server")


class PredictEndpoint(Resource):
    @swagger.operation(
        responseClass=PredictResult.__name__,
        nickname='predict',
        responseMessages=[
            {'code': 400, 'message': 'Input required'},
            {'code': 400, 'message': 'JSON format not valid'},
            {'code': 500, 'message': 'Pipeline processing error'},
        ],
        parameters=[
            {
                'name': 'text',
                'description': 'JSON-encoded text',
                'required': True,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'body'
            },
            {
                'name': 'fileType',
                'description': 'JSON-encoded text',
                'required': False,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'body'
            },
        ])
    @marshal_with(PredictResult.resource_fields)
    def post(self):
        """Return a PredictResult object containing predicted license"""
        logger.debug(f'{str(request)} with payload: {request.json}')
        reqs = request.json
        if not reqs:
            raise JsonRequiredError()
        try:
            active_pipeline = PipelineFactory(Path(get_default_model_dir()).resolve()).build_model()
            result = active_pipeline.predict(reqs['text'], reqs.get('fileType', ''))
            return PredictResult(licenses=result)
        except KeyError as e:
            raise JsonInvalidError() from e
        except Exception as e:
            raise PipelineError() from e


class ModelEndpoint(Resource):
    @swagger.operation(
        responseClass=ModelResult.__name__,
        nickname='model',
        responseMessages=[
            {'code': 500, 'message': 'Pipeline processing error'},
        ])
    @marshal_with(ModelResult.resource_fields)
    def get(self):
        """Return a JSON object with current model configuration"""
        logger.debug(f'{str(request)} with payload: {request.json}')
        try:
            active_pipeline = PipelineFactory(Path(get_default_model_dir()).resolve()).build_model()
            model_info = active_pipeline.config_parser._sections
            return ModelResult(model_info=model_info)
        except Exception as e:
            raise PipelineError() from e


class LicenseEndpoint(Resource):
    @swagger.operation(
        responseClass=LicenseResult.__name__,
        nickname='license',
        responseMessages=[
            {'code': 400, 'message': 'Input required'},
            {'code': 400, 'message': 'JSON format not valid'},
            {'code': 500, 'message': 'Pipeline processing error'},
        ],
        parameters=[
            {
                'name': 'licenseName',
                'description': 'JSON-encoded text',
                'required': True,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'body'
            },
        ])
    @marshal_with(LicenseResult.resource_fields)
    def post(self):
        """Return a JSON object with license name and license text"""
        logger.debug(f'{str(request)} with payload: {request.data}')
        reqs = request.json
        if not reqs:
            raise JsonRequiredError()
        try:
            active_pipeline = PipelineFactory(Path(get_default_model_dir()).resolve()).build_model()
            license_name = reqs['licenseName']
            license_text = active_pipeline.get_license_text(license_name)
            return LicenseResult(license_name, license_text)
        except KeyError as e:
            raise JsonInvalidError() from e
        except Exception as e:
            raise PipelineError() from e