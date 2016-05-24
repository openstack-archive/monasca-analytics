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

import copy
import json
import logging
import os
import unittest

from main.config import const
from main.dsl import interpreter
from main.exception import dsl as dsl_err
from main.exception import monanas as mon_err
from main.source import iptables_markov_chain as ipt_src
from main.source import kafka


class TestDSLInterpreter(unittest.TestCase):

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
        self.test_config_path = os.path.join(current_dir,
                                             "../resources/test_json.json")
        self.tmp_save_file = "my_config.json"
        self.setup_logging()
        self.inter = interpreter.DSLInterpreter()

    def tearDown(self):
        if os.path.exists(self.tmp_save_file):
            os.remove(self.tmp_save_file)

    def test_cmd_create(self):
        comp_id = self.inter.execute_string("A = IPTablesSource")
        self.assertEqual("src1", comp_id)
        self.assertEqual({"A": "src1"}, self.inter.mappings)
        self.assertEqual(ipt_src.IPTablesSource.get_default_config(),
                         self.inter.dsl._config[const.SOURCES]["src1"])

    def test_cmd_create_inexistent(self):
        self.assertRaises(mon_err.MonanasNoSuchClassError,
                          self.inter.execute_string,
                          "A = fakeModule")

    def test_cmd_connect(self):
        self.inter.execute_string("A = IPTablesSource")
        self.inter.execute_string("B = IptablesIngestor")
        self.assertTrue(self.inter.execute_string("A -> B"))
        self.assertListEqual(["ing1"],
                             self.inter.dsl._config[const.CONNECTIONS]["src1"])

    def test_cmd_connect_connected(self):
        self.inter.execute_string("A = IPTablesSource")
        self.inter.execute_string("B = IptablesIngestor")
        self.inter.execute_string("A -> B")
        self.assertFalse(self.inter.execute_string("A -> B"))
        self.assertListEqual(["ing1"],
                             self.inter.dsl._config[const.CONNECTIONS]["src1"])

    def test_cmd_connect_inexistent(self):
        self.assertRaises(dsl_err.DSLInterpreterException,
                          self.inter.execute_string, "A -> B")

    def test_cmd_connect_forbidden(self):
        self.inter.execute_string("A = IPTablesSource")
        self.inter.execute_string("B = PickIndexVoter")
        self.assertRaises(dsl_err.DSLInvalidConnection,
                          self.inter.execute_string, "A -> B")

    def test_cmd_disconnect(self):
        self.inter.execute_string("A = IPTablesSource")
        self.inter.execute_string("B = IptablesIngestor")
        self.inter.execute_string("A -> B")
        self.assertTrue(self.inter.execute_string("A !-> B"))
        self.assertListEqual([],
                             self.inter.dsl._config[const.CONNECTIONS]["src1"])

    def test_cmd_load(self):
        self.inter.execute_string("load(" + self.test_config_path + ")")
        with open(self.test_config_path) as f:
            expected_config = json.loads(f.read())
        self.assertEqual(expected_config, self.inter.dsl._config)

    def test_cmd_save(self):
        self.inter.execute_string("save(" + self.tmp_save_file + ")")
        self.inter.execute_string("load(" + self.tmp_save_file + ")")
        self.inter.execute_string("A = IPTablesSource")
        self.inter.execute_string("save()")
        expected = const.get_default_base_config()
        expected[const.SOURCES]["src1"] = ipt_src.IPTablesSource.\
            get_default_config()
        expected[const.CONNECTIONS]["src1"] = []
        with open(self.tmp_save_file) as f:
            saved_config = json.loads(f.read())
        self.assertEqual(expected, saved_config)
        pass

    def test_cmd_save_as(self):
        self.inter.execute_string("save(" + self.tmp_save_file + ")")
        with open(self.tmp_save_file) as f:
            saved_config = json.loads(f.read())
        self.assertEqual(const.get_default_base_config(), saved_config)

    def test_cmd_remove(self):
        self.inter.execute_string("A = IPTablesSource")
        self.inter.execute_string("rm(A)")
        self.assertEqual({}, self.inter.dsl._config[const.SOURCES])

    def test_cmd_remove_inexistent(self):
        self.assertRaises(dsl_err.DSLInterpreterException,
                          self.inter.execute_string, "rm(A)")

    def test_cmd_remove_connected(self):
        self.inter.execute_string("A = IPTablesSource")
        self.inter.execute_string("B = IptablesIngestor")
        self.inter.execute_string("A -> B")
        self.assertRaises(dsl_err.DSLExistingConnection,
                          self.inter.execute_string, "rm(A)")

    def test_cmd_modify_to_valid_float(self):
        self.inter.execute_string("A = IPTablesSource")
        self.assertTrue(self.inter.execute_string(
            "A.params.server_sleep_in_seconds = 0.02"))
        self.assertEqual({
            "module": "IPTablesSource",
            "params": {
                "server_sleep_in_seconds": 0.02
            }}, self.inter.dsl._config[const.SOURCES]["src1"])

    def test_cmd_modify_to_invalid_float(self):
        self.inter.execute_string("A = IPTablesSource")
        self.assertFalse(self.inter.execute_string(
            "A.params.server_sleep_in_seconds = 1.2"))

    def test_cmd_modify_int(self):
        self.inter.execute_string("A = KafkaSource")
        self.assertTrue(self.inter.execute_string(
            "A.params.zk_port = 1234"))
        expected = copy.deepcopy(kafka.KafkaSource.get_default_config())
        expected["params"]["zk_port"] = 1234
        self.assertEqual(expected,
                         self.inter.dsl._config[const.SOURCES]["src1"])

    def test_cmd_modify_str(self):
        self.inter.execute_string("A = KafkaSource")
        self.assertTrue(self.inter.execute_string(
            "A.params.zk_host = my_host"))
        expected = copy.deepcopy(kafka.KafkaSource.get_default_config())
        expected["params"]["zk_host"] = "my_host"
        self.assertEqual(expected,
                         self.inter.dsl._config[const.SOURCES]["src1"])

    def test_get_id_from_name(self):
        self.inter.execute_string("A = IPTablesSource")
        _id = self.inter._get_id("A")
        self.assertEqual("src1", _id)

    def test_get_id_from_id(self):
        self.inter.execute_string("A = IPTablesSource")
        _id = self.inter._get_id("src1")
        self.assertEqual("src1", _id)
