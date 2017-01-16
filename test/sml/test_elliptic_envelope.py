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
from sklearn import covariance

from monasca_analytics.sml import elliptic_envelope
from test.util_for_testing import MonanasTestCase

logger = logging.getLogger(__name__)


class TestEllipticEnvelope(MonanasTestCase):

    def setUp(self):
        super(TestEllipticEnvelope, self).setUp()
        self.ee_sml = elliptic_envelope.EllipticEnvelope(
            "fakeid", {"module": "fake", "nb_samples": 1000})

    def tearDown(self):
        super(TestEllipticEnvelope, self).tearDown()

    def get_testing_data(self):
        a = np.random.uniform(size=1000)
        b = np.random.uniform(size=1000)
        c = np.random.uniform(size=1000)
        d = np.random.uniform(size=1000)
        return np.array([a, b, c, d]).T

    def test_generate_train_test_sets(self):
        data = self.get_testing_data()
        train, test = self.ee_sml._generate_train_test_sets(data, 0.6)
        self.assertEqual(600, len(train))
        self.assertEqual(400, len(test))

    def test_learn_structure(self):
        data = self.get_testing_data()
        clf = self.ee_sml.learn_structure(data)
        self.assertIsInstance(clf, covariance.EllipticEnvelope)
