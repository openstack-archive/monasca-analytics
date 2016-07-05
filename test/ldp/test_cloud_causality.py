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

from monasca_analytics.ldp import cloud_causality as cloud
from test.util_for_testing import MonanasTestCase


class TestCloudCausalityLDP(MonanasTestCase):

    def setUp(self):
        super(TestCloudCausalityLDP, self).setUp()

    def tearDown(self):
        super(TestCloudCausalityLDP, self).tearDown()

    def test_get_default_config(self):
        default_config = cloud.CloudCausalityLDP.get_default_config()
        cloud.CloudCausalityLDP.validate_config(default_config)
        self.assertEqual("CloudCausalityLDP", default_config["module"])
