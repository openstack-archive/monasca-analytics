#!/usr/bin/env python

# Copyright (c) 2016 Hewlett Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

import numpy as np
import six
from sklearn import svm
import voluptuous

import monasca_analytics.banana.typeck.type_util as type_util
import monasca_analytics.component.params as params
from monasca_analytics.sml import base
from monasca_analytics.util import validation_utils as vu

logger = logging.getLogger(__name__)

ANOMALY = -1
NON_ANOMALY = 1
N_SAMPLES = 1000
OUTLIERS_FRACTION = 0.10


class SvmOneClass(base.BaseSML):
    """Anomaly detection based on the SVM one class algorithm"""

    def __init__(self, _id, _config):
        super(SvmOneClass, self).__init__(_id, _config)
        self._nb_samples = int(_config["nb_samples"])

    @staticmethod
    def validate_config(_config):
        svm_schema = voluptuous.Schema({
            "module": voluptuous.And(six.string_types[0],
                                     vu.NoSpaceCharacter()),
            "nb_samples": voluptuous.Or(float, int)
        }, required=True)
        return svm_schema(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": SvmOneClass.__name__,
            "nb_samples": N_SAMPLES
        }

    @staticmethod
    def get_params():
        return [
            params.ParamDescriptor("nb_samples", type_util.Number(), N_SAMPLES)
        ]

    def number_of_samples_required(self):
        return self._nb_samples

    def _generate_train_test_sets(self, samples, ratio_train):
        num_samples_train = int(len(samples) * ratio_train)
        X_train = np.array(samples[:num_samples_train])
        X_test = np.array(samples[num_samples_train:])
        return X_train, X_test

    def learn_structure(self, samples):
        X_train, X_test = self._generate_train_test_sets(samples, 0.75)
        logger.info("Training with " + str(len(X_train)) +
                    "samples; testing with " + str(len(X_test)) + " samples.")
        svm_detector = svm.OneClassSVM(nu=0.95 * OUTLIERS_FRACTION + 0.05,
                                       kernel="rbf", gamma=0.1)
        svm_detector.fit(X_train)
        Y_test = svm_detector.predict(X_test)
        num_anomalies = Y_test[Y_test == -1].size
        logger.info("Found " + str(num_anomalies) +
                    " anomalies in testing set")
        return svm_detector
