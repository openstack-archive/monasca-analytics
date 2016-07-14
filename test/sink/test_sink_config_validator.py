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

import unittest
import voluptuous

import monasca_analytics.sink.sink_config_validator as validator

kafka = validator.validate_kafka_sink_config


class SinkConfigValidatorTest(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self._valid_config = {
            "module": "KafkaSink",
            "host": "127.0.0.1",
            "port": 9092,
            "topic": "transformed_data"
        }

    def test_validate_kafka_sink_valid_config(self):
        try:
            kafka(self._valid_config)
        except voluptuous.Invalid as e:
            self.fail(e.__str__())

    def test_validate_kafka_sink_invalid_module(self):
        invalid_config = self._valid_config
        invalid_config["module"] = "invalid_module"
        self.assertRaises(voluptuous.Invalid, kafka, invalid_config)

    def test_validate_kafka_sink_invalid_host(self):
        invalid_config = self._valid_config
        invalid_config["host"] = "invalid host"
        self.assertRaises(voluptuous.Invalid, kafka, invalid_config)

    def test_validate_kafka_sink_invalid_port(self):
        invalid_config = self._valid_config
        invalid_config["port"] = "invalid_port"
        self.assertRaises(voluptuous.Invalid, kafka, invalid_config)

    def test_validate_kafka_sink_invalid_topic(self):
        invalid_config = self._valid_config
        invalid_config["topic"] = "invalid topic"
        self.assertRaises(voluptuous.Invalid, kafka, invalid_config)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
