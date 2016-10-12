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

from monasca_analytics.ldp.monasca_aggregate import MonascaAggregateLDP
from test.util_for_testing import gen_metric
from test.util_for_testing import MonanasTestCase


class TestMonascaAggregateLDP(MonanasTestCase):

    def setUp(self):
        super(TestMonascaAggregateLDP, self).setUp()
        self.all_metrics = [
            gen_metric("memory", 1.5, 0, "h1"),
            gen_metric("memory", 2.0, 1, "h1"),
            gen_metric("memory", 1.0, 0, "h2"),
            gen_metric("memory", 3.0, 1, "h2"),
        ]

    def tearDown(self):
        super(TestMonascaAggregateLDP, self).tearDown()

    def _reduce(self, fn, iterable):
        # iterable = map(lambda i: {"metric": {"value": i}}, iterable)
        cnt = len(iterable)
        acc = fn[0](iterable[0], cnt)
        for index in range(1, cnt):
            acc = fn[1](acc, iterable[index], cnt)
        return acc

    def _conf(self, fn_name):
        return {
            "func": fn_name
        }

    def test_reducer_avg(self):
        avg_reducer = MonascaAggregateLDP.select_reducer(self._conf("avg"))
        self.assertEqual(
            self._reduce(avg_reducer, [1.0, 2.0, 3.0, 6.0]),
            3
        )

    def test_reducer_max(self):
        max_reducer = MonascaAggregateLDP.select_reducer(self._conf("max"))
        self.assertEqual(
            self._reduce(max_reducer, [1, 2, 3, 6]),
            6
        )

    def test_reducer_min(self):
        min_reducer = MonascaAggregateLDP.select_reducer(self._conf("min"))
        self.assertEqual(
            self._reduce(min_reducer, [1, 2, 3, 6]),
            1
        )

    def test_reducer_sum(self):
        sum_reducer = MonascaAggregateLDP.select_reducer(self._conf("sum"))
        self.assertEqual(
            self._reduce(sum_reducer, [1, 2, 3, 6]),
            12
        )

    def test_reducer_cnt(self):
        cnt_reducer = MonascaAggregateLDP.select_reducer(self._conf("cnt"))
        self.assertEqual(
            self._reduce(cnt_reducer, [1, 2, 3, 6]),
            4
        )

    def test_aggregate_with_avg(self):
        reducer = MonascaAggregateLDP.select_reducer(self._conf("avg"))
        res = MonascaAggregateLDP.aggregate(self.all_metrics, reducer, "_avg")
        res = map(lambda m: m["metric"]["value"], res)
        self.assertEqual(res, [1.25, 2.5])

    def test_aggregate_with_min(self):
        reducer = MonascaAggregateLDP.select_reducer(self._conf("min"))
        res = MonascaAggregateLDP.aggregate(self.all_metrics, reducer, "_min")
        res = map(lambda m: m["metric"]["value"], res)
        self.assertEqual(res, [1.0, 2.0])

    def test_aggregate_with_max(self):
        reducer = MonascaAggregateLDP.select_reducer(self._conf("max"))
        res = MonascaAggregateLDP.aggregate(self.all_metrics, reducer, "_max")
        res = map(lambda m: m["metric"]["value"], res)
        self.assertEqual(res, [1.5, 3.0])

    def test_aggregate_with_sum(self):
        reducer = MonascaAggregateLDP.select_reducer(self._conf("sum"))
        res = MonascaAggregateLDP.aggregate(self.all_metrics, reducer, "_sum")
        res = map(lambda m: m["metric"]["value"], res)
        self.assertEqual(res, [2.5, 5.0])

    def test_aggregate_with_cnt(self):
        reducer = MonascaAggregateLDP.select_reducer(self._conf("cnt"))
        res = MonascaAggregateLDP.aggregate(self.all_metrics, reducer, "_cnt")
        res = map(lambda m: m["metric"]["value"], res)
        self.assertEqual(res, [2, 2])
