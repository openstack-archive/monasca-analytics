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

from monasca_analytics.sml import random_forest_classifier
from test.util_for_testing import MonanasTestCase

logger = logging.getLogger(__name__)


class TestRandomForestClassifier(MonanasTestCase):

    def setUp(self):
        super(TestRandomForestClassifier, self).setUp()
        self.rf_sml = random_forest_classifier.RandomForestClassifier(
            "fakeid", {"module": "fake", "nb_samples": 1000})

    def tearDown(self):
        super(TestRandomForestClassifier, self).tearDown()

    def get_testing_data(self):
        a = np.random.uniform(size=1000)
        b = np.random.uniform(size=1000)
        c = np.random.uniform(size=1000)
        d = np.random.uniform(size=1000)
        labels = np.random.randint(2, size=1000)
        return np.array([a, b, c, d, labels]).T

    def test_generate_train_test_sets(self):
        data = self.get_testing_data()
        X_train, X_train_labeled, X_test, X_test_labeled =\
            self.rf_sml._generate_train_test_sets(data, 0.6)
        self.assertEqual(600, len(X_train))
        self.assertEqual(600, len(X_train_labeled))
        self.assertEqual(400, len(X_test))
        self.assertEqual(400, len(X_test_labeled))

    def test_learn_structure(self):
        data = self.get_testing_data()
        clf = self.rf_sml.learn_structure(data)
        self.assertIsInstance(clf, ensemble.RandomForestClassifier)
