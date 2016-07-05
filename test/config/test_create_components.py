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

import os

from monasca_analytics.config import const
from monasca_analytics.config import creation
from monasca_analytics.exception import monanas as err
import monasca_analytics.util.common_util as cu
from test.mocks import sml_mocks
from test.util_for_testing import MonanasTestCase


class CreateComponentsTest(MonanasTestCase):

    def setUp(self):
        """
        Keep a copy of the original functions that will be mocked, then
        mock them, reset variables, and initialize ML_Framework.
        """
        super(CreateComponentsTest, self).setUp()
        self._backup_functions()
        self._mock_functions()
        sml_mocks.sml_mocks.reset()
        self.init_sml_config()

    def tearDown(self):
        """
        Restore the potentially mocked functions to the original ones
        """
        super(CreateComponentsTest, self).tearDown()
        self._restore_functions()

    def _backup_functions(self):
        self.original_get_class_by_name = cu.get_class_by_name

    def _restore_functions(self):
        cu.get_class_by_name = self.original_get_class_by_name

    def _mock_functions(self):
        cu.get_class_by_name = sml_mocks.mock_get_class_by_name

    def init_sml_config(self):
        """
        Initialize the ML_Framework object with the test_json config
        """
        current_dir = os.path.dirname(__file__)
        test_json_file = os.path.join(current_dir,
                                      "../resources/test_json.json")
        self._config = cu.parse_json_file(test_json_file)

    def test_create_component_by_module(self):
        sml_mocks.sml_mocks.reset()
        component_id = "ing1"
        component_config = {"module": "ingestor_module", "sink_id": 1}
        creation._create_component_by_module(component_id, component_config,
                                             "ingestors")
        self.assert_only_instantiated("ingestor_module")

    def test_create_component_by_module_inexistent_module(self):
        sml_mocks.sml_mocks.reset()
        component_id = "inex1"
        component_config = {"module": "inexistent_module"}
        self.assertRaises(
            err.MonanasNoSuchClassError,
            creation._create_component_by_module,
            component_id, component_config, "ingestors")
        self.assert_instantiated_no_classes()

    def test_create_components_by_module(self):
        sml_mocks.sml_mocks.reset()
        creation._create_comps_by_module(const.LDPS, self._config)
        self.assert_only_instantiated("ldp_module1")

    def test_create_components_by_module_inexistent1(self):
        sml_mocks.sml_mocks.reset()
        self._config["voter"] = {"inex1": {"module": "inexistent_voter"}}
        self.assertRaises(err.MonanasNoSuchClassError,
                          creation._create_comps_by_module,
                          "voter", self._config)
        self.assert_instantiated_no_classes()

    def test_create_components_by_module_inexistent2(self):
        sml_mocks.sml_mocks.reset()
        self._config["ingestors"] = {
            "inex2": {"module": "inexistent_ingestor", "param": {}}
        }
        self.assertRaises(err.MonanasNoSuchClassError,
                          creation._create_comps_by_module,
                          "ingestors", self._config)
        self.assert_instantiated_no_classes()

    def test_create_components_by_module_mixed_existance(self):
        sml_mocks.sml_mocks.reset()
        self._config[const.INGESTORS]["inex2"] =\
            {"module": "inexistent_ingestor", "params": {}}
        self.assertRaises(err.MonanasNoSuchClassError,
                          creation._create_comps_by_module,
                          const.INGESTORS, self._config)

    def assert_instantiated_no_classes(self):
        for n in sml_mocks.sml_mocks.instantiated.keys():
            self.assertEqual(0, len(sml_mocks.sml_mocks.instantiated[n]))

    def assert_only_instantiated(self, name):
        self.assertEqual(1, len(sml_mocks.sml_mocks.instantiated[name]))
        for n in sml_mocks.sml_mocks.instantiated.keys():
            if n != name:
                self.assertEqual(0, len(sml_mocks.sml_mocks.instantiated[n]))
