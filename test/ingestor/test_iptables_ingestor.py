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

import json
import logging
import os
import unittest

import numpy as np

from main.ingestor import iptables as ipt_ing
from main.source import iptables_markov_chain as ipt_src


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
        self.rdd_entry = {
            "ctime": "Mon Apr 11 19:59:12 2016",
            "events": [
                {
                    "msg": "OUTPUT -p icmp --icmp-type echo-request -j ACCEPT",
                    "id": "1"},
                {
                    "msg": "OUTPUT -o eth0 -p tcp --sport 80 -j ACCEPT",
                    "id": "1"}
            ]
        }
        self.ip_ing = ipt_ing.IptablesIngestor("fake_id",
                                               {"module": "fake_config"})
        self.ip_ing.set_feature_list(["ssh", "ip", "http", "ping"])

    def tearDown(self):
        pass

    def test_get_default_config(self):
        default_config = ipt_ing.IptablesIngestor.get_default_config()
        ipt_ing.IptablesIngestor.validate_config(default_config)
        self.assertEqual("IptablesIngestor", default_config["module"])

    def test_process_data(self):
        rdd_str = '{"ctime": "Mon Apr 11 19:59:12 2016","events": ['
        for iptable in ipt_src.iptables:
            rdd_str += '{"msg": "' + iptable + '","id": "1"}, '
        rdd_str = rdd_str[:-2] + ']}'
        processed = self.ip_ing._process_data(rdd_str, self.ip_ing._features)
        np.testing.assert_array_equal(
            processed, np.array([2, 4, 2, 4]))
