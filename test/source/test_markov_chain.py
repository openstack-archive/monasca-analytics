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
import logging
import os
import unittest

import schema

from monasca_analytics.source import cloud_markov_chain as cloud
from test.mocks import spark_mocks


class MarkovChainSourceTest(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        self.setup_logging()
        params = {
            "server_sleep_in_seconds": 0.1
        }
        transitions = {
            "web_service": {
                "run=>slow": {
                    0: 0.01,
                    8: 0.2,
                    12: 0.7,
                    14: 0.7,
                    22: 0.3,
                    24: 0.1
                },
                "slow=>run": {
                    0: 1,
                    8: 0.7,
                    12: 0.1,
                    14: 0.1,
                    22: 0.8,
                    24: 0.99
                },
                "stop=>run": 0.5
            },
            "switch": {
                "on=>off": 0.1,
                "off=>on": 0.5
            },
            "host": {
                "on=>off": 0.5,
                "off=>on": 0.1
            },
        }
        self.valid_config = {
            "module": "markov_chain_source",
            "transitions": dict(transitions),
            "triggers": {
                "support": {
                    "get_called": {
                        0: 0.1,
                        8: 0.2,
                        12: 0.8,
                        14: 0.8,
                        22: 0.5,
                        24: 0.0
                    }
                }
            },
            "params": dict(params),
            "graph": {
                "h1:host": ["s1"],
                "h2:host": ["s1"],
                "s1:switch": [],
                "w1:web_service": ["h1"],
                "w2:web_service": ["h2"]
            }
        }
        self.config_extra_param = dict(self.valid_config)
        self.config_extra_param["params"] = dict(params)
        self.config_extra_param["params"]["extra_param"] = "john doe"
        self.config_missing_param = dict(self.valid_config)
        self.config_missing_param["transitions"] = dict(transitions)
        self.config_missing_param["transitions"].pop("host")
        self.config_wrong_type = {
            "module": 123,
            "transitions": dict(self.valid_config["transitions"]),
            "params": dict(params),
            "graph": {}
        }
        self.mcs = cloud.CloudMarkovChainSource("fake_id", self.valid_config)

    def tearDown(self):
        pass

    def test_validate_valid_config(self):
        self.assertEqual(self.valid_config, self.mcs._config)

    def test_validate_config_extra_param(self):
        self.assertRaises(
            schema.SchemaError,
            self.mcs.validate_config,
            self.config_extra_param)

    def test_validate_config_missing_param(self):
        self.assertRaises(
            schema.SchemaError,
            self.mcs.validate_config,
            self.config_missing_param)

    def test_validate_config_wrong_type(self):
        self.assertRaises(
            schema.SchemaError,
            self.mcs.validate_config,
            self.config_wrong_type)

    def test_get_default_config(self):
        default_config = cloud.CloudMarkovChainSource.get_default_config()
        cloud.CloudMarkovChainSource.validate_config(default_config)
        self.assertEqual("CloudMarkovChainSource", default_config["module"])

    def test_create_dstream_created(self):
        ssc = spark_mocks.MockStreamingContext(None, None)
        self.assertIsNotNone(self.mcs.create_dstream(ssc))
        self.mcs.terminate_source()
        self.assertEqual(ssc._host, "localhost")

    def test_create_system(self):
        [support_node] = self.mcs._create_system()
        ws = support_node.dependencies
        self.assertEqual(len(ws), 2)
        ws1 = ws[0]
        self.assertEqual(len(ws1.dependencies), 1)
        ws2 = ws[1]
        self.assertEqual(len(ws2.dependencies), 1)
        hs1 = ws1.dependencies[0]
        self.assertEqual(len(hs1.dependencies), 1)
        hs2 = ws2.dependencies[0]
        self.assertEqual(len(hs2.dependencies), 1)
        self.assertEqual(hs1.dependencies[0], hs2.dependencies[0])


if __name__ == "__main__":
    unittest.main()
