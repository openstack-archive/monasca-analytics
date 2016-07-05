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

from monasca_analytics.spark import aggregator
from test.mocks import spark_mocks
from test.util_for_testing import MonanasTestCase


class BaseAggregatorTest(MonanasTestCase):

    def setUp(self):
        super(BaseAggregatorTest, self).setUp()
        self.da = AggregatorBasicChild(None)
        self.set_mocks()

    def tearDown(self):
        super(BaseAggregatorTest, self).tearDown()

    def set_mocks(self):
        pass

    def test_aggregate_first_time(self):
        dstream1 = spark_mocks.MockDStream(None, None, None)
        self.da.accumulate_dstream_samples(dstream1)
        self.assertEqual(dstream1, self.da._combined_stream)
        self.assertEqual(0, self.da._combined_stream.join_cnt)

    def test_aggregate_with_no_smls(self):
        dstream1 = spark_mocks.MockDStream(None, None, None)
        self.da.accumulate_dstream_samples(dstream1)


class AggregatorBasicChild(aggregator.Aggregator):

    def __init__(self, driver):
        super(AggregatorBasicChild, self).__init__(driver)
        self.accumulation_logic_cnt = 0

    def prepare_final_accumulate_stream_step(self):
        super(AggregatorBasicChild, self)\
            .prepare_final_accumulate_stream_step()
        self.accumulation_logic_cnt += 1
