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

from monasca_analytics.voter import base
from test.util_for_testing import MonanasTestCase


class BaseVoterTest(MonanasTestCase):

    def setUp(self):
        super(BaseVoterTest, self).setUp()
        self.vot = VoterBasicChild("fake_id", "fake_config")

    def tearDown(self):
        super(BaseVoterTest, self).tearDown()

    def test_suggest_structure_no_smls_or_structures(self):
        self.vot.suggest_structure("who", "struct")


class VoterBasicChild(base.BaseVoter):

    def __init__(self, _id, _config):
        self.elect_cnt = 0
        super(VoterBasicChild, self).__init__(_id, _config)

    def elect_structure(self, structures):
        self.elect_cnt += 1

    @staticmethod
    def validate_config(_config):
        pass

    @staticmethod
    def get_default_config():
        return {"module": VoterBasicChild.__name__}

    @staticmethod
    def get_params():
        return []
