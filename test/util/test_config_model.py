import json
import logging
import os
import unittest

import schema

from main.config import validation
from main.util import common_util

logger = logging.getLogger(__name__)


class TestConfigModel(unittest.TestCase):

    def get_config(self):
        current_dir = os.path.dirname(__file__)
        test_json_file = os.path.join(current_dir,
                                      "../resources/test_json.json")
        return common_util.parse_json_file(test_json_file)

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        self.setup_logging()
        self.comp_types = ["sources", "ingestors", "smls",
                           "voters", "ldps", "sinks"]
        self.config = self.get_config()

    def test_validate_config_valid(self):
        ret = validation.validate_config(self.config)
        self.assertIsNone(ret)

    def test_validate_config_missing_key(self):
        for key in self.comp_types:
            del self.config[key]
            self.assertRaises(schema.SchemaError,
                              validation.validate_config, self.config)
            self.config = self.get_config()

    def test_validate_config_extra_key(self):
        self.config = self.get_config()
        self.config["infiltrated"] = "I should not exist"
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)
        self.config = self.get_config()

    def test_validate_config_missing_spark_key(self):
        for key in self.config["spark_config"].keys():
            del self.config["spark_config"][key]
            self.assertRaises(schema.SchemaError,
                              validation.validate_config, self.config)
            self.config = self.get_config()
        del self.config["spark_config"]["streaming"]["batch_interval"]
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)

    def test_validate_config_missing_server_key(self):
        del self.config["server"]["port"]
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)
        self.config = self.get_config()
        del self.config["server"]["debug"]
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)

    def test_validate_config_spark_wrong_format(self):
        self.config["spark_config"]["streaming"][
            "batch_interval"] = "I should not be a string"
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)
        self.config = self.get_config()
        self.config["spark_config"]["appName"] = 123
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)

    def test_validate_config_server_wrong_format(self):
        self.config["server"]["port"] = "I should be an int"
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)
        self.config = self.get_config()
        self.config["server"]["debug"] = 52
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)

    def test_validate_config_spark_extra_parameters(self):
        self.config["spark_config"]["infiltrated"] = "I should not exist"
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)
        self.config = self.get_config()
        self.config["spark_config"]["streaming"][
            "infiltrated"] = "I should not exist"
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)

    def test_validate_config_server_extra_parameters(self):
        self.config["server"]["infiltrated"] = "I should not exist"
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)

    def test_validate_config_wrong_format_components(self):
        for key in self.comp_types:
            self.config[key] = ["I", "should", "be", "a", "dictionary"]
            self.assertRaises(schema.SchemaError,
                              validation.validate_config, self.config)
            self.config = self.get_config()
            for comp_id in self.config[key].keys():
                self.config[key][comp_id] = ["I", "should", "be", "a", "dict"]
                self.assertRaises(schema.SchemaError,
                                  validation.validate_config, self.config)
                self.config = self.get_config()

    def test_validate_config_wrong_format_connections(self):
        self.config["connections"] = ["I", "should", "be", "a", "dictionary"]
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)
        self.config = self.get_config()
        for comp_id in self.config["connections"].keys():
                self.config["connections"][comp_id] = {"I": "should",
                                                       "be": "a list"}
                self.assertRaises(schema.SchemaError,
                                  validation.validate_config, self.config)
                self.config = self.get_config()

    def test_validate_connections_data_models(self):
        self.config["connections"]["mod1"] = ["src1"]
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)

    def test_validate_connections_wrong_dest(self):
        wrong_destinations = {
            "src1": ["src1", "src2", "agg1", "sml1",
                     "vot1", "sin1", "sin2"],
            "src2": ["src1", "src2", "agg1", "sml1",
                     "vot1", "sin1", "sin2"],
            "ing1": ["src1", "src2", "ing1", "sml1", "vot1", "ldp1"],
            "agg1": ["src1", "src2", "ing1", "agg1",
                     "vot1", "ldp1"],
            "sml1": ["src1", "src2", "ing1", "sml1",
                     "ldp1"],
            "vot1": ["src1", "src2", "ing1", "agg1", "sml1", "vot1"],
            "sin1": ["src1", "src2", "ing1", "agg1", "sml1",
                     "vot1", "sin1", "sin2", "ldp1"],
            "sin2": ["src1", "src2", "ing1", "agg1", "sml1",
                     "vot1", "sin1", "sin2", "ldp1"],
            "ldp1": ["src1", "src2", "ing1", "agg1", "sml1",
                     "vot1", "ldp1"]
        }
        for from_id in wrong_destinations.keys():
            for dst_id in wrong_destinations[from_id]:
                self.config["connections"][from_id] = [dst_id]
                logger.debug("checking wrong connection: " +
                             from_id + "  --> " + dst_id)
                self.assertRaises(schema.SchemaError,
                                  validation.validate_config, self.config)
                self.config = self.get_config()

    def test_validate_connections_inexisteng_source(self):
        self.config["connections"]["inex"] = ["sin2"]
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)
        self.config = self.get_config()

    def test_validate_connections_inexisteng_dest(self):
        self.config["connections"]["src1"] = ["inex"]
        self.assertRaises(schema.SchemaError,
                          validation.validate_config, self.config)
        self.config = self.get_config()
