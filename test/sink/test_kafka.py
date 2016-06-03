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

import unittest

# This file is name kafkas otherwise it will conflict
# with the global import 'kafka'
import monasca_analytics.sink.kafkas as kf


class KafkaSinkTest(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

        class MockedKafka(object):
            def __init__(self):
                self.has_been_called = False

            def KafkaProducer(self, *_, **kwargs):
                self.has_been_called = True

        self.mock_kafka = MockedKafka()
        self.original_kafka = kf.kafka
        kf.kafka = self.mock_kafka

    def testKafkaSinkInit(self):
        kf.KafkaSink("id", {
            "module": "KafkaSink",
            "params": {
                "host": "localhost",
                "port": 00,
                "topic": "boom",
            }
        })
        self.assertTrue(self.mock_kafka)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        kf.kafka = self.original_kafka

    def test_get_default_config(self):
        default_config = kf.KafkaSink.get_default_config()
        kf.KafkaSink.validate_config(default_config)
        self.assertEqual("KafkaSink", default_config["module"])

if __name__ == "__main__":
    unittest.main()
