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

import voluptuous

from monasca_analytics.source import kafka
from test.mocks import spark_mocks
from test.util_for_testing import MonanasTestCase


class KafkaSourceTest(MonanasTestCase):

    def _mock_functions(self):
        kafka.kafka.KafkaUtils = spark_mocks.MockKafkaUtils

    def setUp(self):
        super(KafkaSourceTest, self).setUp()
        self._mock_functions()
        self.valid_config = {
            "module": "kafka",
            "params": {
                "zk_host": "my_host",
                "zk_port": 1234,
                "group_id": "my_group_id",
                "topics": {"topic1": 1, "topic2": 2}
            }
        }
        self.config_extra_param = {
            "module": "kafka",
            "params": {
                "zk_host": "my_host",
                "zk_port": 1234,
                "group_id": "my_group_id",
                "topics": {"topic1": 1, "topic2": 2},
                "infiltrated": "wrong_param"
            }
        }
        self.config_missing_param = {
            "module": "kafka",
            "params": {
                "zk_host": "my_host",
                "group_id": "my_group_id",
                "topics": {"topic1": 1, "topic2": 2}
            }
        }
        self.config_wrong_type = {
            "module": 123,
            "params": {
                "zk_host": "my_host",
                "zk_port": 1234,
                "group_id": "my_group_id",
                "topics": {"topic1": 1, "topic2": 2}
            }
        }
        self.config_missing_params = {"module": "file"}
        self.ks = kafka.KafkaSource("fake_id", self.valid_config)

    def tearDown(self):
        super(KafkaSourceTest, self).tearDown()

    def test_validate_valid_config(self):
        self.assertEqual(self.valid_config, self.ks._config)

    def test_validate_config_extra_param(self):
        self.assertRaises(
            voluptuous.Invalid,
            self.ks.validate_config,
            self.config_extra_param)

    def test_validate_config_wrong_type(self):
        self.assertRaises(
            voluptuous.Invalid,
            self.ks.validate_config,
            self.config_wrong_type)

    def test_validate_config_missing_params(self):
        self.assertRaises(
            voluptuous.Invalid,
            self.ks.validate_config,
            self.config_missing_params)

    def test_get_default_config(self):
        default_config = kafka.KafkaSource.get_default_config()
        kafka.KafkaSource.validate_config(default_config)
        self.assertEqual("KafkaSource", default_config["module"])

    def test_before_bind_source_dstream_created(self):
        ssc = spark_mocks.MockStreamingContext(None, None)
        self.assertIsNotNone(self.ks.create_dstream(ssc))
