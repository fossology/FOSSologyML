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
Script that converts raw data records in mongodb (file_raw) into deduplicated records (file)
"""

import logging
from typing import Type, Optional

from database import MongoDB
from documents import DocumentConstructionError, DocumentConversionError
from documents import Documents
from utils import log_progress, root_logger

logger = logging.getLogger(__name__)


def map_document(src_doc: Type[Documents.FileRaw]) -> Optional[Type[Documents.File]]:
    """
    Returns mapped source document and reraises potential AttributeErrors
    wrapped in custom :class:`model_generation.data.documents.DocumentConversionError`
    :param src_doc:
    :return:
    """
    try:
        return src_doc.convert_document()
    except AttributeError as e:
        raise DocumentConversionError(f'{src_doc} must implement function convert_document()') from e


def convert_data(src_collection: Type[Documents.FileRaw], dst_collection: Type[Documents.File]):
    """
    Convert entries of :class:`model_generation.data.documents.Documents.FileRaw` to :class:`model_generation.data.documents.Documents.File`
    Each record of :class:`model_generation.data.documents.Documents.File` or its subclasses has unique :attribute: path and
    :attribute licenses of :type list containing all the license findings found for given path in
    the original collection of :class:`model_generation.data.documents.Documents.FileRaw`
    """
    if src_collection == dst_collection:
        raise DocumentConversionError('Source and destination collections must be different')

    with db.connect():
        logger.info(f'Connected to: {db.get_connection_info()}')
        logger.info(f'Converting: {src_collection.__name__} ({db.get_collection_size(src_collection)})'
                    f' -> {dst_collection.__name__} ({db.get_collection_size(dst_collection)})')

    docs = src_collection.objects()
    total_count = docs.count()
    for current_count, src_doc in enumerate(docs):
        log_progress(current_count, total_count)

        try:
            mapped_doc = map_document(src_doc)
        except (DocumentConversionError, DocumentConstructionError) as e:
            logger.warning(f'Skipping: {src_doc} because of: {e}')
            continue

        mapped_doc.create_or_update()

    with db.connect():
        logger.info(f'Total {dst_collection.__name__} count: ({db.get_collection_size(dst_collection)})')
        logger.info(f'Documents.Conclusion count: ({db.get_collection_size(Documents.Conclusion)})')
        logger.info(f'Documents.License count: ({db.get_collection_size(Documents.License)})')


if __name__ == '__main__':
    logger = root_logger('convert_data', logging.INFO)
    try:
        db = MongoDB()  # credentials for MongoDB can be set up here
        convert_data(Documents.FileRaw, Documents.File)
        logger.info('Success')
    except Exception as e:
        logger.info(e, exc_info=True)
