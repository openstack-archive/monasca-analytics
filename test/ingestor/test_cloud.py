import json
import logging
import os
import unittest

from main.ingestor import cloud


class TestIptablesIngestor(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        self.setup_logging()

    def tearDown(self):
        pass

    def test_get_default_config(self):
        default_config = cloud.CloudIngestor.get_default_config()
        cloud.CloudIngestor.validate_config(default_config)
        self.assertEqual("CloudIngestor", default_config["module"])
