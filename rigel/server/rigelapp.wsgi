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
Serves as wsgi endpoint for the apache virtualhost when the server is started with apache with the fossology vagrant box.
"""

import os


def application(apache_environ, start_response):
    from rigel.server.runserver import return_app_object

    os.environ['RIGEL_DIR'] = apache_environ['RIGEL_DIR']
    server = return_app_object()
    return server.app(apache_environ, start_response)
