#!/usr/bin/env python
# -*- encoding: utf-8 -*-
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
Script used for testing the License Classifier on Nomos testdata

"""

import logging
import json 

import click
import click_log
from pathlib import Path
from rigel import utils as utils
from rigel.cli.prediction_logic import ServerPredictor, LocalPredictor
from rigel.pipeline.pipeline_factory import PipelineFactory

from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import hamming_loss,  accuracy_score
from sklearn.metrics import classification_report

logger = logging.getLogger("rigel-cli")
click_log.basic_config(logger)

@click.command()
@click.option('--model_path', '-m', type=click.Path(exists=True), help='Input path to directory with model. Default model located under your $HOME/rigel/models/')
@click.option('--quiet', '-q', is_flag=False, help='Suppress logging to console')

def main(model_path: Path, quiet: bool):
    le = MultiLabelBinarizer(sparse_output=True)

    model_path = Path(model_path).resolve() if model_path else utils.get_default_model_dir()
    prediction_logic = LocalPredictor(PipelineFactory(model_path).build_model()) # to predict local
   
    # Open json file containing filename and actual license
    f = open('test_data.json',)
  
    # returns JSON object as 
    # a dictionary
    files = json.load(f)
    act_pred_lic = []   # temp array to store actual license at even position & predicted license at odd position
    
    for i in range(len(files.keys())):
        act_pred_lic.append(files[str(i)]["licenses"])  #appending actual license
        input_path = "testdata/"+files[str(i)]["file_name"]  #path of file
        act_pred_lic.append(lic_predictor(input_path, model_path, quiet, prediction_logic)) # appending prediction
    
    act_pred_lic = le.fit_transform(act_pred_lic)
    y_train = act_pred_lic[::2] #stores actual licenses
    predictions = act_pred_lic[1::2] #stores predictions on data
    
    print("***Accuracy: ",accuracy_score(y_train, predictions),"***")
    print("***Classification Report***")
    print(classification_report(y_train, predictions, target_names=list(le.classes_)))

def lic_predictor(input_path: Path, model_path: Path, quiet: bool, prediction_logic):
    """
    Function to predict license on the given givel file using the given model_path

    """
    utils.setup_logger(logger, quiet)
    files = utils.get_file_list(input_path)
    result = [prediction_logic.predict(file) for file in files]
    return result[0].licenses

if __name__ == '__main__':  
    main()
