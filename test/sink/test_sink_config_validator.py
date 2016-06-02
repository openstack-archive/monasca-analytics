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

import schema
import unittest

import monasca_analytics.sink.sink_config_validator as validator

kafka = validator.validate_kafka_sink_config


class SinkConfigValidatorTest(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self._valid_config = {
            "module": "KafkaSink",
            "params": {
                "host": "127.0.0.1",
                "port": 9092,
                "topic": "transformed_data"
            }
        }

    def test_validate_kafka_sink_config(self):
        try:
            kafka(self._valid_config)
        except schema.SchemaError as e:
            self.fail(e.__str__())

        invalid_config = self._valid_config
        invalid_config["module"] = "invalid_module"
        self.assertRaises(schema.SchemaError, kafka, invalid_config)
        invalid_config = self._valid_config
        invalid_config["params"]["host"] = "invalid host"
        self.assertRaises(schema.SchemaError, kafka, invalid_config)
        invalid_config = self._valid_config
        invalid_config["params"]["port"] = "invalid_port"
        self.assertRaises(schema.SchemaError, kafka, invalid_config)
        invalid_config = self._valid_config
        invalid_config["params"]["topic"] = "invalid topic"
        self.assertRaises(schema.SchemaError, kafka, invalid_config)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
