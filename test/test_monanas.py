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

import os

from monasca_analytics.exception import monanas as err
import monasca_analytics.monanas as mnn
import monasca_analytics.spark.driver as driver
import monasca_analytics.util.common_util as cu
from test.mocks import sml_mocks
from test.mocks import spark_mocks
from test.util_for_testing import MonanasTestCase


class MonanasTest(MonanasTestCase):

    def setUp(self):
        """
        Keep a copy of the original functions that will be mocked, then
        mock them, reset variables, and initialize ML_Framework.
        """
        super(MonanasTest, self).setUp()
        self._backup_functions()
        self._mock_functions()
        sml_mocks.sml_mocks.reset()
        self.init_sml_config()

    def tearDown(self):
        """
        Restore the potentially mocked functions to the original ones
        """
        super(MonanasTest, self).tearDown()
        self._restore_functions()

    def _backup_functions(self):
        self.original_kill = mnn.os.kill
        self.original_get_class_by_name = cu.get_class_by_name
        self.original_SparkContext = driver.pyspark.SparkContext
        self.original_StreamingContext = \
            driver.streamingctx.streaming.StreamingContext
        self.original_Aggregator = driver.agg.Aggregator

    def _restore_functions(self):
        cu.get_class_by_name = self.original_get_class_by_name
        mnn.os.kill = self.original_kill
        driver.pyspark.SparkContext = self.original_SparkContext
        driver.streamingctx.streaming.StreamingContext = \
            self.original_StreamingContext
        driver.agg.Aggregator = self.original_Aggregator

    def _mock_functions(self):
        cu.get_class_by_name = sml_mocks.mock_get_class_by_name
        mnn.os.kill = sml_mocks.mock_kill
        driver.pyspark.SparkContext = spark_mocks.MockSparkContext
        driver.streamingctx.streaming.StreamingContext = \
            spark_mocks.MockStreamingContext
        driver.agg.Aggregator = sml_mocks.MockClass_aggr_module

    def init_sml_config(self):
        """
        Initialize the ML_Framework object with the test_json config
        """
        current_dir = os.path.dirname(__file__)
        test_json_file = os.path.join(current_dir, "resources/test_json.json")
        config = cu.parse_json_file(test_json_file)
        self.mlf = mnn.Monanas(config)

    def test_is_streaming(self):
        self.assertFalse(self.mlf.is_streaming())
        self.mlf._is_streaming = True
        self.assertTrue(self.mlf.is_streaming())
        self.mlf._is_streaming = False
        self.assertFalse(self.mlf.is_streaming())

    def test_start_streaming_no_param(self):
        self.mlf.start_streaming()
        self.assertTrue(self.mlf.is_streaming())

    def assert_stopped_streaming_state(self, ssc=None):
        if ssc:
            self.assertEqual(1, ssc.stopped_cnt)
        self.assertFalse(self.mlf.is_streaming())

    def test_stop_streaming(self):
        self.mlf.start_streaming()
        self.mlf.stop_streaming()

    def test_stop_streaming_no_streaming(self):
        self.mlf.start_streaming()
        self.mlf.stop_streaming()
        self.assertRaises(err.MonanasAlreadyStoppedStreaming,
                          self.mlf.stop_streaming)

    def test_stop_streaming_and_terminate_from_init_state(self):
        self.assertFalse(sml_mocks.sml_mocks.killed)
        self.mlf.stop_streaming_and_terminate()
        self.assertTrue(sml_mocks.sml_mocks.killed)
        self.assert_stopped_streaming_state()

    def test_stop_streaming_and_terminate_from_streaming_state(self):
        self.assertFalse(sml_mocks.sml_mocks.killed)
        self.mlf.start_streaming()
        self.mlf.stop_streaming_and_terminate()
        self.assertTrue(sml_mocks.sml_mocks.killed)

    def test_stop_streaming_and_terminate_from_stopped_state(self):
        self.assertFalse(sml_mocks.sml_mocks.killed)
        self.mlf.start_streaming()
        self.mlf.stop_streaming()
        self.mlf.stop_streaming_and_terminate()
        self.assertTrue(sml_mocks.sml_mocks.killed)
