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

from typing import List

from rigel.pipeline.enums import MimeType
from rigel.pipeline.sk_pipeline import SKLearnPipeline


class SpecialSKLearnPipeline(SKLearnPipeline):
    pipeline_name = 'sklearn_special_cases'

    def __init__(self, config_parser, dataloader):
        super().__init__(config_parser, dataloader)
        self.special_case_problems = {}
        self.pipeline_name = SpecialSKLearnPipeline.pipeline_name

    def load(self):
        super().load()
        # special-cases is a config.ini section where the options are the cases to be loaded into pipeline
        special_cases = self.config_parser['special-cases']['cases'].split(',')
        self.special_case_problems = {case: self._build_problem(case) for case in special_cases}

    def predict(self, text: str, file_type: str = MimeType.UNKNOWN) -> List:
        """
        2-3 step prediction logic: license findings are being predicted as in
        :meth:`rigelcli.pipeline.sk_pipeline.SKLearnPipeline.predict`. But if there are findings with special sub-cases
        (any problem with a name different than "SP", "DP" or "MP"), another classifier is called for each occurrence
        in the current prediction result to further specify the correct sub-case. If no license with special cases
        appears in the prediction result, this step is skipped.
        :param text: The file content to be analyzed
        :param file_type: What kind of file this is (see UNIX "file" command output)
        :return: A list of license findings for this file
        """
        result = super().predict(text, file_type)

        precise_labels = {}
        for case in self.special_case_problems.keys():
            if case in result:
                precise_labels[case] = self.special_case_problems[case].predict(self.words) or case

        mapped_result = []
        for l in result:
            if l in precise_labels:
                mapped_result += precise_labels[l]
            else:
                mapped_result += [l]
        return mapped_result

    def save(self, problems=None):
        if not problems:
            problems = [self.single_label_problem,
                        self.multi_label_problem,
                        self.dual_problem] + list(self.special_case_problems.values())

        self.config_parser['special-cases'] = {
            "cases": ','.join(set(map(lambda p: p.name, problems)) - {"SP", "MP", "DP"})
        }
        super().save(problems)
