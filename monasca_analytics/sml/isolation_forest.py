#!/usr/bin/env python

# Copyright (c) 2016 FUJITSU LIMITED
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
from sklearn import ensemble
import voluptuous

from monasca_analytics.sml.base import BaseSML
from monasca_analytics.util.validation_utils import NoSpaceCharacter

logger = logging.getLogger(__name__)

ANOMALY = -1
NON_ANOMALY = 1
N_SAMPLES = 1000


class IsolationForest(BaseSML):
    """Anomaly detection based on the IsolationForest algorithm"""

    def __init__(self, _id, _config):
        super(IsolationForest, self).__init__(_id, _config)
        self._nb_samples = int(_config['nb_samples'])

    @staticmethod
    def validate_config(_config):
        isolation_schema = voluptuous.Schema({
            'module': voluptuous.And(
                basestring, NoSpaceCharacter()),
            'nb_samples': voluptuous.Or(float, int)
        }, required=True)
        return isolation_schema(_config)

    @staticmethod
    def get_default_config():
        return {
            'module': IsolationForest.__name__,
            'nb_samples': N_SAMPLES
        }

    @staticmethod
    def get_params():
        return [
            params.ParamDescriptor('nb_samples', type_util.Number(), N_SAMPLES)
        ]

    def number_of_samples_required(self):
        return self._nb_samples

    def _generate_train_test_sets(self, samples, ratio_train):
        num_samples_train = int(len(samples) * ratio_train)
        X_train = np.array(samples[:num_samples_train])
        X_test = np.array(samples[num_samples_train:])
        return X_train, X_test

    def _get_best_detector(self, train):
        detector = ensemble.IsolationForest()
        detector.fit(train)
        return detector

    def learn_structure(self, samples):
        X_train, X_test = self._generate_train_test_sets(samples, 0.75)
        logger.info('Training with ' + str(len(X_train)) +
                    'samples; testing with ' + str(len(X_test)) + ' samples.')

        if_detector = self._get_best_detector(X_train)
        Y_test = if_detector.predict(X_test)

        num_anomalies = Y_test[Y_test == ANOMALY].size
        logger.info('Found ' + str(num_anomalies) +
                    ' anomalies in testing set')
        return if_detector
