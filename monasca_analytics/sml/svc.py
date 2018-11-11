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
import six
from sklearn.metrics import classification_report
from sklearn import svm
import voluptuous

from monasca_analytics.sml.base import BaseSML
from monasca_analytics.util.validation_utils import NoSpaceCharacter

logger = logging.getLogger(__name__)

ANOMALY = 1
NON_ANOMALY = 0
N_SAMPLES = 1000


class Svc(BaseSML):
    """Anomaly detection based on the SVC algorithm"""

    def __init__(self, _id, _config):
        super(Svc, self).__init__(_id, _config)
        self._nb_samples = int(_config['nb_samples'])

    @staticmethod
    def validate_config(_config):
        svc_schema = voluptuous.Schema({
            'module': voluptuous.And(six.string_types[0],
                                     NoSpaceCharacter()),
            'nb_samples': voluptuous.Or(float, int)
        }, required=True)
        return svc_schema(_config)

    @staticmethod
    def get_default_config():
        return {
            'module': Svc.__name__,
            'nb_samples': N_SAMPLES
        }

    def get_params():
        return[
            params.ParamDescriptor('nb_samples', type_util.Number(), N_SAMPLES)
        ]

    def number_of_samples_required(self):
        return self._nb_samples

    def _generate_train_test_sets(self, samples, ratio_train):
        num_samples_train = int(len(samples) * ratio_train)

        data, labels = np.hsplit(samples, [-1])
        X_train = np.array(data[:num_samples_train])
        _labels = np.array(labels[:num_samples_train])
        X_train_label = _labels.ravel()
        X_test = np.array(data[num_samples_train:])
        _labels = np.array(labels[num_samples_train:])
        X_test_label = _labels.ravel()
        return X_train, X_train_label, X_test, X_test_label

    def _get_best_detector(self, train, label):
        detector = svm.SVC(kernel='rbf')
        detector.fit(train, label)
        return detector

    def learn_structure(self, samples):
        X_train, X_train_label, X_test, X_test_label = \
            self._generate_train_test_sets(samples, 0.75)
        logger.info('Training with ' + str(len(X_train)) +
                    'samples; testing with ' + str(len(X_test)) + ' samples.')

        svc_detector = self._get_best_detector(X_train, X_train_label)
        Y_test = svc_detector.predict(X_test)

        num_anomalies = Y_test[Y_test == ANOMALY].size
        logger.info('Found ' + str(num_anomalies) +
                    ' anomalies in testing set')

        logger.info('Confusion Matrix: \n{}'.
                    format(classification_report(
                        X_test_label,
                        Y_test,
                        target_names=['no', 'yes'])))
        return svc_detector
