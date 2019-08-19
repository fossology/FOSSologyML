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
Database class(es)
"""

import logging
import os
from contextlib import contextmanager
from dotenv import find_dotenv, load_dotenv
import mongoengine as me

from utils import sint

logger = logging.getLogger(__name__)


class Database(object):

    def connect(self):
        raise NotImplementedError

    def get_collection_size(self, *collection, **query):
        raise NotImplementedError

    def get_connection_info(self):
        raise NotImplementedError


class MongoDB(Database):
    """
    Manages connections to rigel's MongoDB containing metadata for training documents.
    Connection configuration needs to be put inside a .env file:
    MONGODB_HOST:                   hostname/IP
    MONGODB_PORT:                   port (mongo default: 27017)
    MONGODB_APPLICATION_DATABASE:   database name (usually rigel)
    MONGODB_APPLICATION_USERNAME:   database user
    MONGODB_APPLICATION_PASSWORD:   password for database user
    """

    def __init__(self, db=None, host=None, port=None, username=None, password=None):
        load_dotenv(find_dotenv())
        if db:
            os.environ['MONGODB_APPLICATION_DATABASE'] = db
        if host:
            os.environ['MONGODB_HOST'] = host
        if port:
            os.environ['MONGODB_PORT'] = port
        if username:
            os.environ['MONGODB_APPLICATION_USERNAME'] = username
        if password:
            os.environ['MONGODB_APPLICATION_PASSWORD'] = password

    @contextmanager
    def connect(self):
        """
        Usage:
        with db.connect() as client:
            # access db (e.g. with :class:`model_generation.data.documents.Documents.File`)
        # db connection is closed automatically
        :return: a :mod:`mongoengine.connection` client
        """
        client = me.connect(db=os.getenv('MONGODB_APPLICATION_DATABASE'),
                            host=os.getenv('MONGODB_HOST'),
                            port=sint(os.getenv('MONGODB_PORT')),
                            username=os.getenv('MONGODB_APPLICATION_USERNAME'),
                            password=os.getenv('MONGODB_APPLICATION_PASSWORD'),
                            serverSelectionTimeoutMS=3000)
        try:
            logger.debug(f'Connected to {self.get_connection_info()}')
            yield client
        finally:
            client.close()

    def get_collection_size(self, *collection, **query):
        """
        Get the total number of documents in a list of collections that correspond to a certain query.
        :param collection: The list of collections to be analyzed
        :param query: This query comes in the form of keyword arguments (e.g. path="/some/path", tags="LRW") which
        are directly passed to mongoengine
        :return: The number of documents returned by all queries (see MongoDB's count() method)
        """
        with self.connect():
            return sum([sint(item.objects(**query).count()) for item in collection])

    def get_connection_info(self):
        db = me.connection.get_db()
        return {'address': db.client.address, 'database': db.name}

    def reset_connection_references(*collection):
        """
        Warning, will reset the global references to all db connections.
        Only use thread safe and when you know what you are doing.
        :param collection:
        :return:
        """
        me.connection._dbs = {}
        me.connection._connections = {}
        me.connection._connection_settings = {}
        for item in collection:
            item._collection = None


if __name__ == '__main__':
    pass
