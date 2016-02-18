#!/usr/bin/env python

import json
import logging
import os
import unittest

from main.util import math


class MathTest(unittest.TestCase):

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

    def test_interp1(self):
        table = [(0, 1.), (1, 1.), (2, 3)]
        self.assertAlmostEqual(math.interpolate_1d(table, 0), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 0.), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 1.), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 0.5), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 0.7), 1.)
        self.assertAlmostEqual(math.interpolate_1d(table, 2.), 3.)
        self.assertAlmostEqual(math.interpolate_1d(table, 1.5), 2.)


if __name__ == "__main__":
    unittest.main()
