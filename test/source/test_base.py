import json
import logging
import os
import unittest

from test.mocks import sources


class BaseSourceTest(unittest.TestCase):
    """
    Class that tests the BaseDataSource. It uses the Mock as a testing target,
    because it extends the abstract class BaseIngestor, so the base logic
    can be tested.
    """

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        self.setup_logging()
        self.bs = sources.MockBaseSource("fake_id", "fake_config")

    def tearDown(self):
        pass

    def test_validate_called(self):
        self.assertEqual(1, sources.MockBaseSource.validation_cnt)
