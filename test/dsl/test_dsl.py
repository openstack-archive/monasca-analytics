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

import schema

from main.config import const
from main.dsl.dsl import MonanasDSL
from main.exception import dsl as dsl_err
from main.exception import monanas as mon_err


class TestMonanasDSL(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def get_test_config_file_path(self):
        current_dir = os.path.dirname(__file__)
        return os.path.join(current_dir, "../resources/test_json.json")

    def setUp(self):
        self.setup_logging()
        config_file_path = self.get_test_config_file_path()
        self.dsl = MonanasDSL(config_file_path)
        self.original_config = copy.deepcopy(self.dsl._config)
        self.testing_new_source_config = {
            "module": "KafkaSource",
            "params": {
                "zk_host": "myHost",
                "zk_port": 1234,
                "group_id": "myGroupId",
                "topics": {
                    "myTopic1": 1,
                    "myTopic2": 2
                }
            }
        }
        self.tmp_file = "tmp_config_file.json"

    def tearDown(self):
        if os.path.exists(self.tmp_file):
            os.remove(self.tmp_file)

    def test_generate_id(self):
        self.assertEqual("src4", self.dsl._generate_id(const.SOURCES))
        self.assertEqual("ing2", self.dsl._generate_id(const.INGESTORS))
        self.assertEqual("sml2", self.dsl._generate_id(const.SMLS))
        self.assertEqual("vot2", self.dsl._generate_id(const.VOTERS))
        self.assertEqual("snk3", self.dsl._generate_id(const.SINKS))
        self.assertEqual("ldp2", self.dsl._generate_id(const.LDPS))
        self.assertEqual("src5", self.dsl._generate_id(const.SOURCES))
        self.assertEqual("ing3", self.dsl._generate_id(const.INGESTORS))
        self.assertEqual("sml3", self.dsl._generate_id(const.SMLS))
        self.assertEqual("vot3", self.dsl._generate_id(const.VOTERS))
        self.assertEqual("snk4", self.dsl._generate_id(const.SINKS))
        self.assertEqual("ldp3", self.dsl._generate_id(const.LDPS))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_generate_id_wrong_type(self):
        self.assertRaises(KeyError, self.dsl._generate_id, "wrong_type")

    def test_is_connected(self):
        self.assertTrue(self.dsl._is_connected("src1"))
        self.assertFalse(self.dsl._is_connected("src2"))
        self.assertTrue(self.dsl._is_connected("ing1"))
        self.assertTrue(self.dsl._is_connected("sml1"))
        self.assertTrue(self.dsl._is_connected("vot1"))
        self.assertTrue(self.dsl._is_connected("snk1"))
        self.assertTrue(self.dsl._is_connected("snk2"))
        self.assertTrue(self.dsl._is_connected("ldp1"))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_component_defined(self):
        self.assertTrue(self.dsl._component_defined("src1"))
        self.assertFalse(self.dsl._component_defined("fake_id"))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_validate_connection_by_ids(self):
        self.assertTrue(self.dsl._validate_connection_by_ids("src1", "ing1"))
        self.assertTrue(self.dsl._validate_connection_by_ids("src1", "ldp1"))
        self.assertFalse(self.dsl._validate_connection_by_ids("src2", "sml1"))
        self.assertFalse(self.dsl._validate_connection_by_ids("ing1", "vot1"))
        self.assertTrue(self.dsl._validate_connection_by_ids("ldp1", "snk1"))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_add_component(self):
        new_id = self.dsl.add_component(self.testing_new_source_config)
        self.assertEqual("src4", new_id)
        expected_config = self.original_config
        expected_config[const.SOURCES]["src4"] = self.testing_new_source_config
        expected_config[const.CONNECTIONS]["src4"] = []
        self.assertEqual(expected_config, self.dsl._config)

    def test_add_component_string(self):
        conf_str = json.dumps(self.testing_new_source_config)
        new_id = self.dsl.add_component(conf_str)
        self.assertEqual("src4", new_id)
        expected_config = self.original_config
        expected_config[const.SOURCES]["src4"] = self.testing_new_source_config
        expected_config[const.CONNECTIONS]["src4"] = []
        self.assertEqual(expected_config, self.dsl._config)

    def test_add_component_wrong_config(self):
        del (self.testing_new_source_config["params"]["zk_port"])
        self.assertRaises(schema.SchemaError,
                          self.dsl.add_component,
                          self.testing_new_source_config)
        self.assertEqual(self.original_config, self.dsl._config)

    def test_add_component_wrong_module(self):
        self.testing_new_source_config["module"] = "fake_module"
        self.assertRaises(mon_err.MonanasNoSuchClassError,
                          self.dsl.add_component,
                          self.testing_new_source_config)
        self.assertEqual(self.original_config, self.dsl._config)

    def test_modify_component(self):
        self.assertTrue(self.dsl.modify_component(
            "src3", ["params", "server_sleep_in_seconds"], 0.02))
        expected_config = self.original_config
        expected_config[const.SOURCES]["src3"]["params"][
            "server_sleep_in_seconds"] = 0.02
        self.assertEqual(expected_config, self.dsl._config)

    def test_modify_component_inexistent(self):
        self.assertFalse(self.dsl.modify_component(
            "src8", ["params", "server_sleep_in_seconds"], 0.02))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_modify_component_to_invalid_config(self):
        self.assertFalse(self.dsl.modify_component(
            "src3", ["fake", "fake_param"], 123))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_modify_dictionary_new_path(self):
        original = self.original_config["voters"]["vot1"]
        modified = self.dsl._modify_dictionary(
            original, ["params", "param1", "subparam1A"], "new_value")
        expected = {
            "module": "voter_module",
            "params": {
                "param1": {
                    "subparam1A": "new_value"
                }
            }
        }
        self.assertEqual(expected, modified)

    def test_modify_dictioinary_overwrite_value(self):
        original = self.original_config["sources"]["src1"]
        modified = self.dsl._modify_dictionary(
            original, ["params", "param1"], "new_value")
        expected = {
            "module": "src_module1",
            "params": {
                "param1": "new_value",
                "param2": "val2",
                "model_id": 3
            }
        }
        self.assertEqual(expected, modified)

    def test_modify_dictionary_overwrite_path(self):
        original = self.original_config["sources"]["src1"]
        modified = self.dsl._modify_dictionary(
            original, ["params"], "new_value")
        expected = {
            "module": "src_module1",
            "params":  "new_value"
        }
        self.assertEqual(expected, modified)

    def test_remove_unconnected_component(self):
        self.assertTrue(self.dsl.remove_component("src2"))
        expected_config = self.original_config
        del(expected_config[const.SOURCES]["src2"])
        del(expected_config[const.CONNECTIONS]["src2"])
        self.assertEqual(expected_config, self.dsl._config)

    def test_remove_connected_component(self):
        self.assertRaises(dsl_err.DSLExistingConnection,
                          self.dsl.remove_component, "src1")
        self.assertEqual(self.original_config, self.dsl._config)

    def test_remove_component_wrong_id(self):
        self.assertFalse(self.dsl.remove_component("fake_id"))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_connect_component_new_allowed(self):
        self.assertTrue(self.dsl.connect_components("src2", "ing1"))
        expected_config = self.original_config
        expected_config[const.CONNECTIONS]["src2"].append("ing1")
        self.assertEqual(self.original_config, self.dsl._config)

    def test_connect_existing(self):
        self.assertFalse(self.dsl.connect_components("src1", "ing1"))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_connect_component_new_forbidden(self):
        self.assertRaises(dsl_err.DSLInvalidConnection,
                          self.dsl.connect_components, "src1", "vot1")
        self.assertEqual(self.original_config, self.dsl._config)

    def test_disconnect(self):
        self.assertTrue(self.dsl.disconnect_components("src1", "ing1"))
        expected_config = self.original_config
        expected_config[const.CONNECTIONS]["src1"] = ["ldp1"]
        self.assertEqual(self.original_config, self.dsl._config)

    def test_disconnect_inexistent_components(self):
        self.assertFalse(self.dsl.disconnect_components("fake_1", "fake_2"))
        self.assertFalse(self.dsl.disconnect_components("fake_id", "snk1"))
        self.assertFalse(self.dsl.disconnect_components("src1", "fake_id"))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_disconnect_inexistent_connection(self):
        self.assertFalse(self.dsl.disconnect_components("src2", "ing1"))
        self.assertEqual(self.original_config, self.dsl._config)

    def test_save_configuration_overwrite_no_file(self):
        self.assertTrue(
            self.dsl.save_configuration(self.tmp_file, overwrite_file=True))
        self.dsl._config = None
        self.dsl.load_configuration(self.tmp_file)
        self.assertEqual(self.original_config, self.dsl._config)

    def test_save_configuration_not_overwrite_no_file(self):
        self.assertTrue(
            self.dsl.save_configuration(self.tmp_file, overwrite_file=False))
        self.dsl._config = None
        self.dsl.load_configuration(self.tmp_file)
        self.assertEqual(self.original_config, self.dsl._config)

    def _create_dirty_fyle(self, fname):
        with open(fname, "w") as f:
            f.write("This content may be overwritten")

    def test_save_configuration_overwrite_file(self):
        self._create_dirty_fyle(self.tmp_file)
        self.assertTrue(
            self.dsl.save_configuration(self.tmp_file, overwrite_file=True))
        self.dsl._config = None
        self.dsl.load_configuration("tmp_config_file.json")
        self.assertEqual(self.original_config, self.dsl._config)

    def test_save_configuration_not_overwrite_file(self):
        self._create_dirty_fyle(self.tmp_file)
        old_size = os.stat(self.tmp_file).st_size
        self.assertFalse(
            self.dsl.save_configuration(self.tmp_file, overwrite_file=False))
        self.assertEqual(old_size, os.stat(self.tmp_file).st_size)
