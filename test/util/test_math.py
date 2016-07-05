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

from monasca_analytics.util import math
from test.util_for_testing import MonanasTestCase


class MathTest(MonanasTestCase):

    def setUp(self):
        super(MathTest, self).setUp()

    def tearDown(self):
        super(MathTest, self).tearDown()

    def test_interp1(self):
        table = [(0, 1.), (1, 1.), (2, 3)]
        self.assertAlmostEqual(math.interpolate_1d(table, 0), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 0.), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 1.), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 0.5), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 0.7), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 2.), 3.)
        self.assertAlmostEqual(math.interpolate_1d(table, 1.5), 2.)
