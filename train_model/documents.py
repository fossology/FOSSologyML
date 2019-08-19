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
Object Document Mapping (ODM) Classes
"""

import logging
from pathlib import Path
from typing import Optional

from mongoengine import *

from utils import get_data_dir
from rigel.pipeline.enums import *

logger = logging.getLogger(__name__)


class AbsFinding:
    """
    An AbsFinding is an abstract class, that provides default functionality implementation for ScannerFindings.
    To implement a MyNewFinding subclass implement it as:
    "class MyNewFinding(:class:`model_generation.data.documents.AbsFinding`, :class:`model_generation.data.documents.Documents.File`)"
    and add the source -> Document class mapping to :attr:`model_generation.data.documents.Documents.map`
    """

    def __new__(cls, *args, **kwargs):
        if cls is AbsFinding:
            raise TypeError("AbsFinding class may not be instantiated")
        return object.__new__(cls)

    def create_or_update(self):
        try:
            existing_document = self.__class__.objects.get(path=self.path)
            existing_document.modify(add_to_set__licenses=self.licenses)
        except DoesNotExist:
            self.save()

    def get_file_path(self):
        return Path(utils.get_data_dir() / 'conclusions' / self.path)


class Documents:
    map = {
        Source.NOMOS.value: 'NomosFinding',
        Source.NINKA.value: 'NinkaFinding',
        Source.MONK.value: 'MonkFinding',
        Source.CONCLUSION.value: 'Conclusion',
        Source.BULK.value: 'Bulk',
        Source.BULK_REMOVE.value: 'Bulk',
        Source.LICENSE.value: 'License',
        Source.LICENSE_INDIRECT.value: 'License',
    }

    class FileRaw(Document):
        """
        ODM Object for raw data as exported from FOSSology.
        MongoDB documents in our database are mapped to Python objects using :mod:`mongoengine`.
        Query: FileRaw(<query_key>="query_value", <key_2>="value_2",...).objects()
        """
        path = StringField(required=True)
        source = StringField(required=True)
        licenses = ListField(StringField())
        text = StringField()

        # allow mapping documents with extra fields
        meta = {
            'strict': False,
            'indexes': [
                'path',
                'source',
                'licenses',
            ]
        }

        def __str__(self):
            return f'{self.__class__.__name__}, ObjectId("{self.id}")'

        def convert_document(self) -> Optional['File']:
            """
            Return a mongo document :class:`model_generation.data.documents.Documents.File`.
            :return: the corresponding mongo document if the self.source is in :class:`model_generation.data.enums.Source`,
            None otherwise
            """

            doc = Documents.construct(self.source, self.path, self.licenses)

            # bulk
            if self.source == Source.BULK.value:
                doc.remove = False

            # bulk remove
            elif self.source == Source.BULK_REMOVE.value:
                doc.remove = True

            # license
            elif self.source == Source.LICENSE.value:
                doc.indirect = False
                doc.text = self.text

            # license indirect
            elif self.source == Source.LICENSE_INDIRECT.value:
                doc.indirect = True
                doc.text = self.text

            return doc

    class File(Document):
        """
        MongoDB documents in our database are mapped to Python objects using :mod:`mongoengine`. The mapping is polymorphic
        with this class being the hierarchy root.
        Query: File(<query_key>="query_value", <key_2>="value_2",...).objects() (same API with subclasses of File)
        """
        path = StringField(required=True, unique_with="_cls")
        licenses = ListField(StringField(), required=True)
        mapped_licenses = ListField(StringField())
        tags = ListField(StringField())
        file_type = StringField()
        license_related_words = ListField(StringField())
        no_license_related_words = ListField(StringField())

        meta = {
            'allow_inheritance': True,
            'indexes': [
                '_cls',
                'tags',
                'licenses',
                'mapped_licenses'
            ]
        }

        def create_or_update(self):
            raise NotImplementedError

        def get_file_path(self):
            raise NotImplementedError

        def get_file_type(self):
            return self.file_type

    class NomosFinding(AbsFinding, File):
        """
        NomosFinding document contains the scanner finding of a nomos FOSSology scanner
        """
        pass

    class NinkaFinding(AbsFinding, File):
        """
        NinkaFinding document contains the scanner finding of a ninka FOSSology scanner
        """
        pass

    class MonkFinding(AbsFinding, File):
        """
        MonkFinding document contains the scanner finding of a monk FOSSology scanner
        """
        pass

    class Conclusion(File):
        """
        A Conclusion document contains the final license decision for a single file (either by majority decision from
        ScannerFindings or manual labelling. This is treated as the ground truth for any learning process.
        """

        def create_or_update(self):
            try:
                existing_document = Documents.Conclusion.objects.get(path=self.path)
                existing_document.modify(add_to_set__licenses=self.licenses)
            except DoesNotExist:
                self.save()

        def get_file_path(self):
            return Path(get_data_dir() / 'conclusions' / self.path)

    class Bulk(File):
        """
        A Bulk document is a text snippet that has been manually labelled and added to FOSSology, defining that this
        snipped either:
            - implies a specific license whenever found in a file (:attr:`remove` == False)
            - implies that a specific license cannot be correct for a file containing this text (:attr:`remove` == True)
        """
        remove = BooleanField()
        text = StringField()

        def create_or_update(self):
            try:
                existing_document = Documents.Bulk.objects.get(path=self.path)
                existing_document.modify(add_to_set__licenses=self.licenses)
            except DoesNotExist:
                self.save()

        def get_file_path(self):
            raise NotImplementedError(
                f'{self.__name__} are not saved on filesystem. To see the text call {self.__name__}.text')

    class License(File):
        """
        A License document contains the path to a file with the complete text for a license. If :attr:`indirect` is
        true, the file doesn't contain the whole text but rather a text referencing the license.
        License names are cleaned - stripped of string delimiters (") and extra whitespace before saving them in db.
        """
        indirect = BooleanField(required=True)
        text = StringField()

        def create_or_update(self):
            try:
                licenses = [license.strip("\"").strip() for license in self.licenses]
                existing_document = Documents.License.objects.get(path=self.path)
                existing_document.modify(add_to_set__licenses=licenses)
            except DoesNotExist:
                self.save()

        def get_file_path(self):
            raise NotImplementedError(
                f'{self.__name__} are not saved on filesystem. To see the text call {self.__name__}.text')

    @staticmethod
    def construct(source, path, licenses):
        try:
            targetClass = getattr(Documents, Documents.map[source], None)
            return targetClass(path=path, licenses=licenses)
        except KeyError as e:
            raise DocumentConstructionError(f'source: "{source}" is not mapped in {Documents.map}') from e
        except TypeError as e:
            raise DocumentConstructionError(f'{Documents.map.get(source)} is not implemented in {Documents.map}') from e

    @staticmethod
    def get_document(values: list) -> Optional[File]:
        """
        Construct a mongo document from a list of string entries (usually obtained from a FOSSology .csv dump's columns)
        :param values: [path, conclusion result, scanner result, source, file ID, upload ID],
        see :class:`model_generation.data.enums.Column`
        :return: the corresponding mongo document if the source column is in :class:`model_generation.data.enums.Source`,
        None otherwise
        """

        try:
            path = values[Column.PATH.value]
            source = values[Column.SOURCE.value]

            if source in SCANNERS:
                licenses = [values[Column.SCANNER_RESULT.value]]
            else:
                licenses = [values[Column.CONCLUSION_RESULT.value]]
        except IndexError:
            raise DocumentConstructionError(f'Not enough values to parse!')

        doc = Documents.construct(source, path, licenses)

        # bulk
        if source == Source.BULK.value:
            doc.remove = False

        # bulk remove
        elif source == Source.BULK_REMOVE.value:
            doc.remove = True

        # license
        elif source == Source.LICENSE.value:
            doc.indirect = False

        # license indirect
        elif source == Source.LICENSE_INDIRECT.value:
            doc.indirect = True

        return doc


class DocumentConstructionError(Exception):
    """
    Raised when an error occurs while importing data into the database
    """

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class DocumentConversionError(Exception):
    """
    Raised when an error occurs while converting data within database collections
    """

    def __init__(self, doc, msg=''):
        self.doc = doc
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


if __name__ == '__main__':
    pass
