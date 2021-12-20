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
Script that updates the attributes of Documents in MongoDB.
In particular the following attributes used for training are determined:

mapped_licenses: [list] of licenses that are used as labels (the correct outputs) for machine learning
license_related_words: [list] of words [strings] that are used as inputs for machine learning
no_license_related_words: [list] of words [strings] that are used as inputs for machine learning
tags: [list of special tags that can be used to]

Additionally the Collection Analysis (using analyze_data.py) is performed and saved.

The script runs in parallel, however is computationally intensive and for larger amounts of documents in MongoDB
can take more hours to complete.
"""

import logging
import math
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from os import PathLike, cpu_count

from analyze_data import analyze_in_parallel
from database import MongoDB
from documents import Documents
from dotenv import load_dotenv, find_dotenv
from pymongo import errors
from utils import root_logger, log_progress, get_train_dir, LICENSE_MAPPING_FILENAME

from rigel.pipeline.enums import Tag, Mapping
from rigel.pipeline.preprocessor.preprocessor_nirjas import PreprocessorNirjas
from rigel.utils import get_file_type_from_path, get_file_content

logger = logging.getLogger(__name__)


# update functions

def update_document(document: Documents.File):
    try:
        file_type = get_file_type_from_path(document.get_file_path())
        file_content = get_file_content(document.get_file_path())
        license_related_words = preprocessor.process(document.get_file_path(), file_content)
        no_license_related_wors = preprocessor.process_no_license_relevant_words(document.get_file_path(), file_content)
        mapped_licenses = map_licenses(document.licenses) or document.licenses
        

    except Exception as e:
        logger.warning(f'{e}, {document.id}, {document.path}')
        return

    try:
        document.modify(
            file_type=file_type,
            mapped_licenses=mapped_licenses,
            license_related_words=license_related_words,
            no_license_related_words=no_license_related_wors
        )

    except errors.DocumentTooLarge:
        logger.warning(f'Document too large, attributes will not be stored! {document.id}, {document.path}')

    update_tags(document)


def update_tags(document: Documents.File):
    try:
        document.modify(pull_all__tags=[
            Tag.SINGLE_MAPPED_LICENSE.value,
            Tag.MULTIPLE_MAPPED_LICENSE.value,
            Tag.LRW.value,
            Tag.NO_LRW.value,
        ])

        if len(document.mapped_licenses) == 1:
            document.modify(add_to_set__tags=Tag.SINGLE_MAPPED_LICENSE.value)
        elif len(document.mapped_licenses) > 1:
            document.modify(add_to_set__tags=Tag.MULTIPLE_MAPPED_LICENSE.value)

        if document.license_related_words:
            document.modify(add_to_set__tags=Tag.LRW.value)
        if document.no_license_related_words:
            document.modify(add_to_set__tags=Tag.NO_LRW.value)

    except Exception as e:
        logger.warning(f'{e}, Could not update tags for: {document.id}, {document.path}')


def map_licenses(old_licenses):
    if license_mapping:
        mapped_licenses = set()
        for old_license in old_licenses:
            old_license = old_license.strip("\"").strip()
            new_licenses = license_mapping.get(old_license, [old_license])
            new_licenses = new_licenses if new_licenses else [old_license]
            if Mapping.NO_MAPPED_LICENSE.value in new_licenses:
                break
            else:
                mapped_licenses.update(new_licenses)
        return mapped_licenses


def process_cursor(update_function, skip_n, limit_n, _collection, **query):
    try:
        process_id = skip_n // limit_n
    except ZeroDivisionError:
        logger.info('Exiting: Nothing to update!')
        return 0

    logger.info('[%s] Starting process %d', str(update_function.__name__), process_id)
    with db.connect():
        docs = _collection.objects(**query).timeout(False).skip(skip_n).limit(limit_n)
        docs_count = docs.count(with_limit_and_skip=True)
        try:
            for doc_no, doc in enumerate(docs):
                update_function(doc)

        finally:
            docs._cursor.close()
            logger.info('[%s] Completed process %d', str(update_function.__name__), process_id)

    return docs_count, None


def update(update_function, n_cores, batch_size, collection, **query):
    collection_size = db.get_collection_size(collection, **query)
    batch_size = min(batch_size, collection_size // n_cores)
    if batch_size:
        skips = range(0, collection_size, batch_size)
        db.reset_connection_references(collection)
        logger.info('Running updates on collection: %s (%s) - (no_cores: %d, batch_size: %d, collection_size: %d)',
                    collection.__name__, query, n_cores, batch_size, collection_size)

        with ProcessPoolExecutor(max_workers=n_cores) as executor:
            future_to_chunk = [executor.submit(process_cursor, update_function, skip_n, batch_size, collection, **query)
                               for skip_n in skips]

            current = 0
            for future in as_completed(future_to_chunk):
                current += future.result()[0]
                logger.debug('Thread: %s %s', future, future.result())
                log_progress(current, collection_size, '', num_log_outputs=collection_size)
    else:
        logger.info(f'Query {query} for collection {collection} found {collection_size} documents'
                    f'\nRunning sequentially ...')
        process_cursor(update_function, 0, collection_size, collection, **query)


def load_license_mapping_file(input_filepath: PathLike) -> dict:
    """
    Loads file content of a csv (;) with 2 or more columns into dictionary[column0] = list[column1, column2, ...]
    :param input_filepath:
    :return: License mapping as a dictionary[column0] = list[column1, column2, ...]
    """
    result = None
    try:
        with open(input_filepath) as f:
            result = dict()
            for line_no, line in enumerate(f):
                columns = line.strip().split(';')
                old_license_name = columns[0]
                if old_license_name in result:
                    logger.warning(f'Duplicate license mapping for: {old_license_name} in 1st column, Line: {line_no}')
                new_license_names = [name for name in columns[1:] if name]
                result[old_license_name] = new_license_names
    except Exception as e:
        logger.warning('Loading file content: %s in %s', str(e), str(input_filepath))
        pass

    return result


# end update functions

# functions for tagging the benchmark set

def process_cursor_remove_tag(tag: str, _collection):
    logger.info('Started removing tag %s from %s', tag, _collection)
    with db.connect():
        query = {'tags': tag}
        docs = _collection.objects(**query).timeout(False).only('tags')
        docs_count = docs.count(with_limit_and_skip=True)
        try:
            for doc_no, doc in enumerate(docs):
                log_progress(doc_no, docs_count)
                doc.modify(pull__tags=tag.value)

        finally:
            docs._cursor.close()
            logger.info('Completed removing tag %s from %s', tag, _collection)


def add_tag(collection_analysis, tag, min_samples, factor):
    """
    :param collection_analysis: An object that compounds distribution of license occurrences within the database
    :param tag: Tag you want to distribute
    :param min_samples: Minimal number of license occurences in the whole database, in order to consider worth tagging it
    :param factor: Multiplication Factor used to compute how many tags shall be given for each license computed from original distribution
    """
    license_counts = Counter(collection_analysis.mapped_single_license) + Counter(
        collection_analysis.mapped_multiple_license)
    logger.info(
        f'Tagging with {tag} with factor {factor} on {len(license_counts)} unique licenses with min_samples {min_samples} ')

    logger.info(f'Removing old tags...')
    with db.connect():
        Documents.Conclusion.objects().update(pull__tags=tag)
        db.reset_connection_references(Documents.Conclusion)

    with ProcessPoolExecutor(max_workers=n_cores) as executor:
        futures = [executor.submit(add_tag_for_max_samples, tag, license, count, factor)
                   for license, count in license_counts.items() if count >= min_samples]

        current = 0
        for future in as_completed(futures):
            current += 1
            log_progress(current, len(license_counts))

    with db.connect():
        tagged_docs = Documents.Conclusion.objects(tags=tag)
        db.reset_connection_references(Documents.Conclusion)

    logger.info(f'\nTagged {tagged_docs.count()} documents with {tag}...')


def add_tag_for_max_samples(tag, license, count, factor):
    max_samples = math.ceil(count * factor)
    with db.connect():
        docs = Documents.Conclusion.objects(mapped_licenses=license).order_by('path')
        docs_count = docs.count()
        logger.info(f'{license} Tagging {max_samples} samples with tag for total {docs_count} - {docs._mongo_query}')
        try:
            for i, doc in enumerate(docs):
                if i == max_samples:
                    break
                doc.modify(add_to_set__tags=tag)
                i += 1
        except StopIteration as e:
            pass
        finally:
            logger.info(f'{license} Finished tagging {i} samples with {tag}')
            docs._cursor.close()


# end functions for tagging the benchmark set


if __name__ == '__main__':
    logger = root_logger('update_data', logging.INFO)
    load_dotenv(find_dotenv())
    preprocessor = PreprocessorNirjas()

    try:
        db = MongoDB()  # credentials for MongoDB can be set up here
        n_cores = cpu_count()  # number of processors that shall be used can be set up here

        license_mapping = load_license_mapping_file(get_train_dir() / LICENSE_MAPPING_FILENAME)
        update(update_document, n_cores=n_cores, batch_size=10_000, collection=Documents.Conclusion)

        collection_analysis = analyze_in_parallel(db, n_cores=n_cores, batch_size=10_000,
                                                  collection=Documents.Conclusion)

        collection_analysis.save_statistics(db)
        collection_analysis.save_object()

        # this is useful for validation of the models later, usually the factor is around 0.1 = 10%
        # however for strongly biased sets it might be better to lessen the factor
        add_tag(collection_analysis, tag=Tag.TEST.value, min_samples=10, factor=0.1)

    except Exception as e:
        logger.info(e, exc_info=True)
