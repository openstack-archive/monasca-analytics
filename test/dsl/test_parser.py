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

from monasca_analytics.dsl import const
from monasca_analytics.dsl import parser


class TestMonanasDSL(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        current_dir = os.path.dirname(__file__)
        self.dsl_file_path = os.path.join(current_dir,
                                          "../resources/dsl_code.txt")
        self.setup_logging()

    def tearDown(self):
        pass

    def assert_create(self, info, varname, module):
        self.assertEqual(varname, info[const.CREATE][0])
        self.assertEqual(module, info[const.CREATE][1])

    def assert_modify(self, info, varname, params, value):
        self.assertEqual(varname, info[const.MODIFY][0])
        self.assertListEqual(info[const.MODIFY][1:-1], params)
        self.assertEqual(value, info[const.MODIFY][-1])

    def assert_connect(self, info, varname1, varname2):
        self.assertEqual(varname1, info[const.CONNECT][0])
        self.assertEqual(varname2, info[const.CONNECT][1])

    def assert_disconnect(self, info, varname1, varname2):
        self.assertEqual(varname1, info[const.DISCONNECT][0])
        self.assertEqual(varname2, info[const.DISCONNECT][1])

    def assert_remove(self, info, varname):
        self.assertEqual(varname, info[const.REMOVE][0])

    def assert_load(self, info, filepaht):
        self.assertEqual(filepaht, info[const.LOAD][0])

    def assert_save(self, info):
        self.assertIn(const.SAVE, info)

    def assert_save_as(self, info, filepaht):
        self.assertEqual(filepaht, info[const.SAVE_AS][0])

    def test_parse_create(self):
        info = parser.get_parser().parseString("A = my_module")
        self.assertEqual(1, len(info))
        self.assertItemsEqual([const.CREATE], info[0].keys())
        self.assert_create(info[0], "A", "my_module")

    def test_parse_modify(self):
        info = parser.get_parser().parseString("_A1.params.123._inf- = my.val")
        self.assertEqual(1, len(info))
        self.assertItemsEqual([const.MODIFY], info[0].keys())
        self.assert_modify(info[0], "_A1", ["params", "123", "_inf-"],
                           "my.val")

    def test_parse_connect(self):
        info = parser.get_parser().parseString("_A1->B")
        self.assertEqual(1, len(info))
        self.assertItemsEqual([const.CONNECT], info[0].keys())
        self.assert_connect(info[0], "_A1", "B")

    def test_parse_disconnect(self):
        info = parser.get_parser().parseString("_A1!->B")
        self.assertEqual(1, len(info))
        self.assertItemsEqual([const.DISCONNECT], info[0].keys())
        self.assert_disconnect(info[0], "_A1", "B")

    def test_parse_remove(self):
        info = parser.get_parser().parseString("rM(A)")
        self.assertEqual(1, len(info))
        self.assertItemsEqual([const.REMOVE], info[0].keys())
        self.assert_remove(info[0], "A")

    def test_parse_load(self):
        info = parser.get_parser().parseString("LoAd(_some/path/123.json)")
        self.assertEqual(1, len(info))
        self.assertItemsEqual([const.LOAD], info[0].keys())
        self.assert_load(info[0], "_some/path/123.json")

    def test_parse_save(self):
        info = parser.get_parser().parseString("sAVe()")
        self.assertEqual(1, len(info))
        self.assertItemsEqual([const.SAVE], info[0].keys())
        self.assert_save(info[0])

    def test_parse_save_as(self):
        info = parser.get_parser().parseString("sAVE(/root/0/path_/f.conf)")
        self.assertEqual(1, len(info))
        self.assertItemsEqual([const.SAVE_AS], info[0].keys())
        self.assert_save_as(info[0], "/root/0/path_/f.conf")

    def test_parse_multiline(self):
        info = parser.get_parser().parseString(
            "load(_path/conf.json)\n\nA=MySource1\nA->ing1")
        self.assertEqual(3, len(info))
        self.assert_load(info[0], "_path/conf.json")
        self.assert_create(info[1], "A", "MySource1")
        self.assert_connect(info[2], "A", "ing1")

    def test_parse_comments(self):
        info = parser.get_parser().parseString(
            "load(_path/conf.json)\n#Comment1\nA=MySource1#Comment2\nA->ing1")
        self.assertEqual(3, len(info))
        self.assert_load(info[0], "_path/conf.json")
        self.assert_create(info[1], "A", "MySource1")
        self.assert_connect(info[2], "A", "ing1")

    def test_parse_file(self):
        info = parser.get_parser().parseFile(self.dsl_file_path)
        self.assertEqual(13, len(info))
        self.assert_create(info[0], "A", "CloudMarkovChainSource")
        self.assert_modify(info[1], "A", ["params", "server_sleep_in_seconds"],
                           "0.1")
        self.assert_create(info[2], "B", "CloudIngestor")
        self.assert_create(info[3], "C", "LiNGAM")
        self.assert_modify(info[4], "C", ["params", "threshold"], "0.1")
        self.assert_create(info[5], "D", "PickIndexVoter")
        self.assert_create(info[6], "E", "KafkaSink")
        self.assert_create(info[7], "F", "CloudCausalityLDP")
        self.assert_connect(info[8], "A", "B")
        self.assert_connect(info[9], "A", "F")
        self.assert_connect(info[10], "C", "D")
        self.assert_connect(info[11], "D", "F")
        self.assert_connect(info[12], "F", "E")
