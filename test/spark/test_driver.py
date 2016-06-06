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

import json
import logging
import os
import unittest

from monasca_analytics.config import const
import monasca_analytics.spark.driver as driver
import monasca_analytics.util.common_util as cu
from test.mocks import sml_mocks
from test.mocks import spark_mocks


class DriverExecutorTest(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        """
        Keep a copy of the original functions that will be mocked, then
        mock them, reset variables, and initialize ML_Framework.
        """
        self.setup_logging()
        self._backup_functions()
        self._mock_functions()
        sml_mocks.sml_mocks.reset()
        self.init_sml_config()

    def tearDown(self):
        """
        Restore the potentially mocked functions to the original ones
        """
        self._restore_functions()
        sml_mocks.sml_mocks.reset_connections()

    def _backup_functions(self):
        self.original_get_class_by_name = cu.get_class_by_name
        self.original_SparkContext = driver.pyspark.SparkContext
        self.original_StreamingContext = driver.streaming.StreamingContext
        self.original_Aggregator = driver.agg.Aggregator

    def _restore_functions(self):
        cu.get_class_by_name = self.original_get_class_by_name
        driver.pyspark.SparkContext = self.original_SparkContext
        driver.streaming.StreamingContext = self.original_StreamingContext
        driver.agg.Aggregator = self.original_Aggregator

    def _mock_functions(self):
        cu.get_class_by_name = sml_mocks.mock_get_class_by_name
        driver.pyspark.SparkContext = spark_mocks.MockSparkContext
        driver.streaming.StreamingContext = spark_mocks.MockStreamingContext
        driver.agg.Aggregator = sml_mocks.MockClass_aggr_module

    def init_sml_config(self):
        """
        Initialize the ML_Framework object with the test_json config
        """
        current_dir = os.path.dirname(__file__)
        test_json_file = os.path.join(current_dir,
                                      "../resources/test_json.json")
        config = cu.parse_json_file(test_json_file)
        self.mlf = driver.DriverExecutor(config)

    def assert_got_classes_by_name_once(self):
        self.assertEqual(9, len(sml_mocks.sml_mocks.classes_got_by_name))
        self.assertIn(["src_module1", const.SOURCES],
                      sml_mocks.sml_mocks.classes_got_by_name)
        self.assertIn(["src_module2", const.SOURCES],
                      sml_mocks.sml_mocks.classes_got_by_name)
        self.assertIn(["IPTablesSource", const.SOURCES],
                      sml_mocks.sml_mocks.classes_got_by_name)
        self.assertIn(["ingestor_module", const.INGESTORS],
                      sml_mocks.sml_mocks.classes_got_by_name)
        self.assertIn(["sml_module", const.SMLS],
                      sml_mocks.sml_mocks.classes_got_by_name)
        self.assertIn(["voter_module", const.VOTERS],
                      sml_mocks.sml_mocks.classes_got_by_name)
        self.assertIn(["sink_module1", const.SINKS],
                      sml_mocks.sml_mocks.classes_got_by_name)
        self.assertIn(["sink_module2", const.SINKS],
                      sml_mocks.sml_mocks.classes_got_by_name)
        self.assertIn(["ldp_module1", const.LDPS],
                      sml_mocks.sml_mocks.classes_got_by_name)

    def assert_instantiated_classes_once(self):
        for n in sml_mocks.sml_mocks.instantiated.keys():
            self.assertEqual(1, len(sml_mocks.sml_mocks.instantiated[n]))

    def assert_instantiated_no_classes(self):
        for n in sml_mocks.sml_mocks.instantiated.keys():
            self.assertEqual(0, len(sml_mocks.sml_mocks.instantiated[n]))

    def assert_only_instantiated(self, name):
        self.assertEqual(1, len(sml_mocks.sml_mocks.instantiated[name]))
        for n in sml_mocks.sml_mocks.instantiated.keys():
            if n != name:
                self.assertEqual(0, len(sml_mocks.sml_mocks.instantiated[n]))

    def assert_src_initialized(self, src):
        self.assertEqual(src.get_feature_list_cnt, 1)
        self.assertEqual(src.create_dstream_cnt, 1)

    def assert_src_termintated(self, src):
        self.assertEqual(src.terminate_source_cnt, 1)

    def assert_ingestor(self, ing):
        self.assertEqual(ing.map_dstream_cnt, 1)

    def assert_agg(self, agg):
        self.assertEqual(agg.accumulate_dstream_samples_cnt, 1)
        self.assertEqual(agg.append_sml_cnt, 1)

    def assert_sml(self, sml):
        self.assertEqual(sml.learn_structure_cnt, 1)

    def assert_voter(self, voter):
        self.assertEqual(voter.elect_structure_cnt, 1)

    def assert_sink(self, sink):
        self.assertEqual(sink.sink_dstream_cnt + sink.sink_sml_cnt, 1)

    def assert_sink_dstream(self, sink):
        self.assertEqual(sink.sink_dstream_cnt, 1)

    def assert_sink_ml(self, sink):
        self.assertEqual(sink.sink_sml_cnt, 1)

    def assert_ldp(self, ldp):
        self.assertEqual(ldp.map_dstream_cnt, 1)

    def test_driver_orchestration_at_creation(self):
        """
        Tests that the Monanas constructor checks the config json file,
        gets all the modules classes by name and instantiates them.
        """
        self.assert_got_classes_by_name_once()
        self.assert_instantiated_classes_once()

    def test_pipeline_connected(self):
        self.mlf.start_pipeline()
        self.assert_src_initialized(
            sml_mocks.sml_mocks.instantiated["src_module1"][0])
        self.assert_src_initialized(
            sml_mocks.sml_mocks.instantiated["src_module2"][0])
        self.assert_ingestor(
            sml_mocks.sml_mocks.instantiated["ingestor_module"][0])
        self.assert_agg(self.mlf._orchestrator)
        self.mlf._orchestrator.accumulate_dstream_samples(
            spark_mocks.MockDStream(None, None, None))
        self.mlf._orchestrator.prepare_final_accumulate_stream_step()
        self.assert_sml(sml_mocks.sml_mocks.instantiated["sml_module"][0])
        self.assert_voter(sml_mocks.sml_mocks.instantiated["voter_module"][0])
        self.assert_sink(
            sml_mocks.sml_mocks.instantiated["sink_module1"][0])
        self.assert_sink_ml(
            sml_mocks.sml_mocks.instantiated["sink_module1"][0])

    def test_start_pipeline(self):
        self.mlf.start_pipeline()

    def test_phase2(self):
        self.mlf.start_pipeline()
        self.assertEqual(1, self.mlf._ssc.started_cnt)
        self.mlf._orchestrator.accumulate_dstream_samples(
            spark_mocks.MockDStream(None, None, None))
        self.mlf._orchestrator.prepare_final_accumulate_stream_step()
        self.assert_ldp(
            sml_mocks.sml_mocks.instantiated["ldp_module1"][0])
        self.assert_sink(
            sml_mocks.sml_mocks.instantiated["sink_module2"][0])
        self.assert_sink_dstream(sml_mocks.sml_mocks.instantiated[
                                 "sink_module2"][0])

    def assert_stopped_streaming_state(self, ssc=None):
        if ssc:
            self.assertEqual(1, ssc.stopped_cnt)
        self.assertEqual(None, self.mlf._sc)
        self.assertEqual(None, self.mlf._ssc)

    def test_stop_pipeline(self):
        self.mlf.start_pipeline()
        ssc = self.mlf._ssc
        self.mlf.stop_pipeline()
        self.assert_stopped_streaming_state(ssc)
