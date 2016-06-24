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

import json
import logging.config
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
