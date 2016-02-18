import json
import logging
import os
import unittest

import schema

from main.source import kafka
from test.mocks import spark_mocks


class KafkaSourceTest(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def _mock_functions(self):
        kafka.kafka.KafkaUtils = spark_mocks.MockKafkaUtils

    def setUp(self):
        self.setup_logging()
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
        pass

    def test_validate_valid_config(self):
        self.assertEqual(self.valid_config, self.ks._config)

    def test_validate_config_extra_param(self):
        self.assertRaises(
            schema.SchemaError,
            self.ks.validate_config,
            self.config_extra_param)

    def test_validate_config_missing_dir(self):
        self.assertRaises(
            schema.SchemaError,
            self.ks.validate_config,
            self.config_missing_param)

    def test_validate_config_wrong_type(self):
        self.assertRaises(
            schema.SchemaError,
            self.ks.validate_config,
            self.config_wrong_type)

    def test_validate_config_missing_params(self):
        self.assertRaises(
            schema.SchemaError,
            self.ks.validate_config,
            self.config_missing_params)

    def test_get_default_config(self):
        default_config = kafka.KafkaSource.get_default_config()
        kafka.KafkaSource.validate_config(default_config)
        self.assertEqual("KafkaSource", default_config["module"])

    def test_before_bind_source_dstream_created(self):
        ssc = spark_mocks.MockStreamingContext(None, None)
        self.assertIsNotNone(self.ks.create_dstream(ssc))
