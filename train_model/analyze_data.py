# !/usr/bin/env python
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
Script that generates basic statistical analysis of documents in MongoDB, in particular the counts of licenses are
important and used later in training to define thresholds and limits on selection of training data.

Additionaly a csv file with unique licenses is generated in the training directory.
You can use this file to define the mapping for licenses.
"""

import _pickle as pickle
import logging
import csv
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from os import cpu_count

from database import MongoDB
from documents import Documents
from dotenv import load_dotenv, find_dotenv
from utils import root_logger, log_progress, get_db_analysis_dir, write_license_mapping_file

logger = logging.getLogger(__name__)


class Analysis(object):
    def __init__(self):
        self.file_types = Counter()
        self.mapped_single_license = Counter()
        self.mapped_multiple_license = Counter()
        self.single_license = Counter()
        self.multiple_license = Counter()
        self.tags = Counter()
        self.doc_count = 0

    def append(self, new_analysis: 'Analysis'):
        self.file_types = self.file_types + Counter(new_analysis.file_types)
        self.mapped_single_license = self.mapped_single_license + Counter(new_analysis.mapped_single_license)
        self.mapped_multiple_license = self.mapped_multiple_license + Counter(new_analysis.mapped_multiple_license)
        self.single_license = self.single_license + Counter(new_analysis.single_license)
        self.multiple_license = self.multiple_license + Counter(new_analysis.multiple_license)

        self.tags = self.tags + Counter(new_analysis.tags)
        self.doc_count = self.doc_count + new_analysis.doc_count

    def analyze_document(self, document: Documents.File):
        self.doc_count += 1
        self.analyze_filetype(document)
        self.analyze_mapped_licenses(document)
        self.analyze_licenses(document)
        self.analyze_tags(document)

    def analyze_filetype(self, doc: Documents.File):
        if doc.file_type:
            t = doc.file_type.strip()
        else:
            t = 'None'
        self.file_types.setdefault(t, 0)
        self.file_types[t] += 1

    def analyze_mapped_licenses(self, doc: Documents.File):
        if len(doc.mapped_licenses) == 1:
            self.mapped_single_license.setdefault(doc.mapped_licenses[0], 0)
            self.mapped_single_license[doc.mapped_licenses[0]] += 1

        if len(doc.mapped_licenses) > 1:
            for lic in doc.mapped_licenses:
                self.mapped_multiple_license.setdefault(lic, 0)
                self.mapped_multiple_license[lic] += 1

    def analyze_licenses(self, doc: Documents.File):
        if len(doc.licenses) == 1:
            self.single_license.setdefault(doc.licenses[0], 0)
            self.single_license[doc.licenses[0]] += 1

        if len(doc.licenses) > 1:
            for lic in doc.licenses:
                self.multiple_license.setdefault(lic, 0)
                self.multiple_license[lic] += 1

    def analyze_tags(self, doc: Documents.File):
        for tag in doc.tags:
            self.tags.setdefault(tag, 0)
            self.tags[tag] += 1

    @staticmethod
    def print_sorted_counts(d, topn=None):
        return ['%s : %s' % (item[0], item[1]) for item in Analysis.get_sorted_counts(d, topn)]

    @staticmethod
    def get_sorted_counts(d, topn=None):
        results = [(k, v) for k, v in sorted(d.items(), reverse=True, key=lambda x: x[1])]
        if topn and topn <= len(results):
            return results[:topn]
        return results

    def print_sorted_percentages(self, d, topn=None):
        results = ['%s : %0.2f%%' % (k, v / self.doc_count * 100) for k, v in
                   sorted(d.items(), reverse=True, key=lambda x: x[1])]
        if topn and topn <= len(results):
            return results[:topn]
        return results

    def print_counts(self, topn=None):
        dictionaries = {k: v for k, v in self.__dict__.items() if isinstance(v, Counter)}
        results = ['%s -%s' % (key, self.print_sorted_counts(d, topn)) for key, d in dictionaries.items()]

        return '\n'.join(results)

    def print_percentages(self, total=None, topn=None):
        dictionaries = {k: v for k, v in self.__dict__.items() if isinstance(v, Counter)}
        results = ['%s -%s' % (key, self.print_sorted_percentages(d, topn)) for key, d in dictionaries.items()]

        return '\n'.join(results)


class CollectionAnalysis(Analysis):
    def __init__(self, collection: Documents.File, **query):
        super().__init__()
        self.collection = collection
        self.query = query if query else {}
        self.collection_name = collection.__name__

    def analyze(self):
        docs = self.collection.objects(**self.query)
        doc_count = docs.count()
        logger.info('Running Collection analysis for %s, query: %s (%d)', self.collection_name, self.query, doc_count)

        for doc_no, doc in enumerate(docs):
            log_progress(doc_no, doc_count)
            self.analyze_document(doc)

    def analyze_batch(self, skip_n, limit_n):
        docs = self.collection.objects(**self.query).timeout(False).skip(skip_n).limit(limit_n)
        doc_count = docs.count(with_limit_and_skip=True)
        logger.debug('Running Collection analysis for %s, query: %s (%d)', self.collection_name, self.query, doc_count)

        for doc_no, doc in enumerate(docs):
            self.analyze_document(doc)

    def print_counts(self, topn=None):
        results = ['%s - query: %s - %d' % (str(self.collection_name), str(self.query), self.doc_count)]
        dictionaries = {k: v for k, v in self.__dict__.items() if isinstance(v, Counter)}
        results += ['%s -%s' % (key, self.print_sorted_counts(d, topn)) for key, d in dictionaries.items()]

        return '\n'.join(results)

    def print_percentages(self, total=None, topn=None):
        total = self.doc_count if not total else total
        if total == 0:
            return 'Can not compute percentages if total count = 0'

        results = [
            '%s - query: %s - %0.2f%%' % (str(self.collection_name), str(self.query), self.doc_count / total * 100)]
        dictionaries = {k: v for k, v in self.__dict__.items() if isinstance(v, Counter)}
        results += ['%s -%s' % (key, self.print_sorted_percentages(d, topn)) for key, d in dictionaries.items()]

        return '\n'.join(results)

    def save_statistics(self, db, output_path=None):
        if not output_path:
            output_path = get_db_analysis_dir() / (self.collection_name + '.stat')

        with open(output_path, 'w') as output:
            output.write(
                'Running Database analysis for collection %s, query: %s\n' % (self.collection_name, self.query))
            with db.connect():
                output.write('Connected to: %s\n\n' % db.get_connection_info())
            output.write('Absolute counts:\n\n')
            output.write(self.print_counts())
            output.write('\n\n')
            output.write('Percentage:\n\n')
            output.write(self.print_percentages())

    def save_object(self, output_path=None):
        if not output_path:
            output_path = get_db_analysis_dir() / (self.collection_name + '.pkl')

        with open(output_path, 'wb') as output:
            pickle.dump(self, output, -1)

        logger.info('Collection analysis saved to %s', output_path)

    @staticmethod
    def load_object(input_path):
        logger.info('Loading collection analysis from: %s', input_path)
        with open(input_path, 'rb') as input:
            return pickle.load(input)

    def get_top_mapped_licenses(self, top_n=None):
        single_name, single_count = zip(*Analysis.get_sorted_counts(self.mapped_single_license, top_n))
        multi_name, multi_count = zip(*Analysis.get_sorted_counts(self.mapped_multiple_license, top_n))
        return set(single_name + multi_name)

    def get_mapped_licenses_with_min_samples(self, min_samples):
        result = []

        for license in Analysis.get_sorted_counts(self.mapped_single_license):
            name = license[0]
            count = license[1]
            if count >= min_samples:
                result.append(name)
            else:
                break

        for license in Analysis.get_sorted_counts(self.mapped_multiple_license):
            name = license[0]
            count = license[1]
            if count >= min_samples:
                result.append(name)
            else:
                break

        return set(result)

    def get_set_of_unique_licenses(self):
        license_counts = self.single_license + self.multiple_license
        return set(license_counts.keys())

    def get_set_of_unique_mapped_licenses(self):
        license_counts = self.mapped_single_license + self.mapped_multiple_license
        return set(license_counts.keys())


def analyze_in_parallel(db, n_cores, batch_size, collection, **query):
    collection_size = db.get_collection_size(collection, **query)
    batch_size = min(batch_size, collection_size // n_cores)

    final_analysis = CollectionAnalysis(collection)
    if batch_size:
        skips = range(0, collection_size, batch_size)
        db.reset_connection_references(collection)
        logger.info('Running analysis on collection: %s (%s) - (no_cores: %d, batch_size: %d, collection_size: %d)',
                    collection.__name__, query, n_cores, batch_size, collection_size)

        with ProcessPoolExecutor(max_workers=n_cores) as executor:
            future_to_chunk = [executor.submit(analyze_batch, db, skip_n, batch_size, collection, **query)
                               for skip_n in skips]

            current = 0
            for future in as_completed(future_to_chunk):
                ca = future.result()[0]
                current += ca.doc_count
                final_analysis.append(ca)

                logger.debug('Thread: %s %s', future, future.result())
                log_progress(current, collection_size, '', num_log_outputs=collection_size)
    else:
        logger.info(f'Query {query} for collection {collection} found {collection_size} documents'
                    f'\nRunning sequentially ...')
        analyze_batch(0, collection_size, collection, **query)

    return final_analysis


def analyze_batch(db, skip_n, limit_n, _collection, **query):
    try:
        process_id = skip_n // limit_n
    except ZeroDivisionError:
        logger.info('Exiting: Nothing to update!')
        return 0

    logger.info('[%s] Starting process %d', 'analyze_batch', process_id)

    with db.connect():
        ca = CollectionAnalysis(_collection, **query)
        ca.analyze_batch(skip_n, limit_n)

    logger.info('[%s] Completed process %d', 'analyze_batch', process_id)

    return ca, None


if __name__ == '__main__':
    logger = root_logger('analyze_data', logging.INFO)
    load_dotenv(find_dotenv())

    try:
        db = MongoDB()  # credentials for MongoDB can be set up here
        n_cores = cpu_count()  # number of processors that shall be used can be set up here
        analysis = analyze_in_parallel(db, n_cores=n_cores, batch_size=10_000, collection=Documents.Conclusion)

        logger.info(analysis.print_counts())
        logger.info(analysis.print_percentages())

        analysis.save_statistics(db, output_path=None)
        analysis.save_object(output_path=None)

        write_license_mapping_file(sorted(list(analysis.get_set_of_unique_licenses()), key=lambda s: s.casefold()))

    except Exception as e:
        logger.info(e, exc_info=True)
