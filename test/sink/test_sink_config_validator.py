#!/usr/bin/env python

import schema
import unittest

import main.sink.sink_config_validator as validator

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
