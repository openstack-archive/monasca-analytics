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

from monasca_analytics.ldp.monasca_derivative import MonascaDerivativeLDP
from pyspark.resultiterable import ResultIterable
from test.util_for_testing import gen_metric
from test.util_for_testing import MonanasTestCase


class TestMonascaAggregateLDP(MonanasTestCase):

    def setUp(self):
        super(TestMonascaAggregateLDP, self).setUp()
        self.all_metrics = [
            gen_metric("memory", 1.5, 0, "h1"),
            gen_metric("memory", 2.0, 1, "h1"),
            gen_metric("memory", 1.0, 0, "h1"),
            gen_metric("memory", 3.0, 1, "h1"),
            gen_metric("memory", 1.5, 4, "h1"),
            gen_metric("memory", 2.0, 2, "h1"),
            gen_metric("memory", 1.0, 3, "h1"),
            gen_metric("memory", 3.0, 5, "h1"),
        ]

    def _values(self, values):
        return map(lambda m: m["metric"]["value"], values)

    def tearDown(self):
        super(TestMonascaAggregateLDP, self).tearDown()

    def test_derivative_should_do_nothing_with_1_value(self):
        self.assertEqual(MonascaDerivativeLDP.derivative(
            ResultIterable(self.all_metrics[0:1])),
            [])

    def test_derivative_should_work_on_first_and_last_values(self):
        new_values = MonascaDerivativeLDP.derivative(
            ResultIterable(self.all_metrics[0:2]))
        new_values = self._values(new_values)
        self.assertEqual(new_values,
                         [0.5, 0.5])

    def test_derivative_should_remove_duplicate(self):
        new_values = MonascaDerivativeLDP.derivative(
            ResultIterable(self.all_metrics[0:4]))
        new_values = self._values(new_values)
        self.assertEqual(new_values,
                         [0.5, 0.5])

    def test_derivative_should_work(self):
        new_values = MonascaDerivativeLDP.derivative(
            ResultIterable(self.all_metrics))
        new_values = self._values(new_values)
        self.assertEqual(new_values,
                         [0.5, 0.25, -0.5, -0.25, 1.0, 1.5])
