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

import os
import unittest

from monasca_analytics.config import const
from monasca_analytics.exception import monanas as err
from monasca_analytics.sml import lingam
from monasca_analytics.source import kafka
from monasca_analytics.util import common_util
from monasca_analytics.voter import pick_index
from test import util
from test.util import inheritance as inh


class CommonUtilTest(unittest.TestCase):

    def test_parse_json_file(self):
        current_dir = os.path.dirname(__file__)
        test_json_file = os.path.join(current_dir,
                                      "../resources/test_json.json")
        parsed_json = common_util.parse_json_file(test_json_file)
        self.assertItemsEqual(parsed_json["sources"]["src1"],
                              {"module": "src_module1",
                               "params": {
                                   "param1": "val1",
                                   "param2": "val2",
                                   "model_id": 3}
                               })
        self.assertItemsEqual(parsed_json["ingestors"]["ing1"],
                              {"module": "ingestor_module"})
        self.assertItemsEqual(parsed_json["smls"]["sml1"],
                              {"module": "sml_module"})
        self.assertEqual(parsed_json["voters"]["vot1"],
                         {"module": "voter_module"})
        self.assertItemsEqual(parsed_json["sinks"]["snk1"],
                              {"module": "sink_module1"})
        self.assertItemsEqual(parsed_json["sinks"]["snk2"],
                              {"module": "sink_module2"})
        self.assertItemsEqual(parsed_json["ldps"]["ldp1"],
                              {"module": "ldps_module1"})
        self.assertItemsEqual(parsed_json["connections"],
                              {"src1": ["ing1"],
                               "src2": ["ing1"],
                               "ing1": ["aggr1", "ldp1", "sin1"],
                               "snk1": [],
                               "snk2": [],
                               "sml1": ["vot1", "snk1"],
                               "vot1": ["ldp1", "snk1"],
                               "ldp1": ["snk2"]})
        self.assertItemsEqual(parsed_json["feedback"],
                              {"snk1": ["sml1"],
                               "snk2": ["vot1"]})

    def test_get_class_by_name(self):
        common_util.get_class_by_name("RandomSource", const.SOURCES)

    def test_get_class_by_name_no_such_class(self):
        self.assertRaises(err.MonanasNoSuchClassError,
                          common_util.get_class_by_name,
                          "InventedSource",
                          const.SOURCES)

    def test_get_available_inherited_classes(self):
        children = common_util.get_available_inherited_classes(util,
                                                               inh.Baseclass)
        classes = [source_class.__name__ for source_class in children]
        self.assertItemsEqual(classes,
                              ["Extended_1_1", "Extended_1_2",
                               "Extended_1_3", "Extended_2_1", "Extended_3_1"])

    def test_get_source_class_by_name(self):
        clazz = common_util.get_source_class_by_name("KafkaSource")
        self.assertEqual(clazz, kafka.KafkaSource)

    def test_get_available_source_class_names(self):
        names = common_util.get_available_source_class_names()
        self.assertItemsEqual(
            ['RandomSource', 'KafkaSource',
             'CloudMarkovChainSource', 'IPTablesSource'],
            names)

    def test_get_available_ingestor_class_names(self):
        names = common_util.get_available_ingestor_class_names()
        self.assertItemsEqual(
            ['CloudIngestor', 'IptablesIngestor'],
            names)

    def test_get_sml_class_by_name(self):
        clazz = common_util.get_sml_class_by_name(
            "LiNGAM")
        self.assertEqual(clazz, lingam.LiNGAM)

    def test_get_available_sml_class_names(self):
        names = common_util.get_available_sml_class_names()
        self.assertItemsEqual(
            ['LiNGAM', "SvmOneClass"],
            names)

    def test_get_voter_class_by_name(self):
        clazz = common_util.get_voter_class_by_name(
            "PickIndexVoter")
        self.assertEqual(clazz, pick_index.PickIndexVoter)

    def test_get_available_voter_class_names(self):
        names = common_util.get_available_voter_class_names()
        self.assertItemsEqual(["PickIndexVoter"], names)

    def test_get_available_ldp_class_names(self):
        names = common_util.get_available_ldp_class_names()
        self.assertItemsEqual(["CloudCausalityLDP", "IptablesLDP"], names)
