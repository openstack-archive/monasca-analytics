#!/usr/bin/env python

# Copyright (c) 2016 Hewlett Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not used this file except in compliance with the License. You may obtain
# a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import unittest

import numpy as np

from monasca_analytics.sml import lingam

logger = logging.getLogger(__name__)


class LiNGAMTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_continuous_lingam_algorithm(self):
        b = np.random.laplace(size=500)
        a = np.random.laplace(size=500) + b
        d = np.random.laplace(size=500) + a + b
        c = np.random.laplace(size=500) + d
        data = np.array([a, b, c, d])
        causality_matrix, causal_order =\
            lingam.LiNGAM._discover_structure(data.T)

        logger.debug("\nb deps (should be almost zero): {}"
                     .format(np.sum(np.abs(causality_matrix[1, :]))))
        logger.debug("\ncausality matrix:\n{}".format(causality_matrix))
        self.assertEqual(np.all(causal_order == np.array([1, 0, 3, 2])), True,
                         "Algorithm didn't found the causal order!")

    def test_discrete_set_lingam_algorithm(self):
        b = np.random.laplace(size=500)
        a = np.random.laplace(size=500) + b
        d = np.random.laplace(size=500) + a + b
        c = np.random.laplace(size=500) + d
        data = np.array([a, b, c, d])
        data = np.floor(data)
        causality_matrix, causal_order =\
            lingam.LiNGAM._discover_structure(data.T)

        logger.debug("\nb deps (should be almost zero): {}"
                     .format(np.sum(np.abs(causality_matrix[1, :]))))
        logger.debug("\ncausality matrix:\n{}".format(causality_matrix))
        self.assertEqual(np.all(causal_order == np.array([1, 0, 3, 2])), True,
                         "Algorithm didn't found the causal order!")

    def test_discrete_set_absolute_value_lingam_algorithm(self):
        b = np.random.laplace(size=500)
        a = np.random.laplace(size=500) + b
        d = np.random.laplace(size=500) + a + b
        c = np.random.laplace(size=500) + d
        data = np.array([a, b, c, d])
        data = np.floor(data)
        data = np.abs(data)
        causality_matrix, causal_order =\
            lingam.LiNGAM._discover_structure(data.T)

        logger.debug("\nb deps (should be almost zero): {}"
                     .format(np.sum(np.abs(causality_matrix[1, :]))))
        logger.debug("\ncausality matrix:\n{}".format(causality_matrix))
        self.assertEqual(np.all(causal_order == np.array([1, 0, 3, 2])), True,
                         "Algorithm didn't found the causal order!")

    def test_get_default_config(self):
        default_config = lingam.LiNGAM.get_default_config()
        lingam.LiNGAM.validate_config(default_config)
        self.assertEqual("LiNGAM", default_config["module"])


if __name__ == "__main__":
    unittest.main()
