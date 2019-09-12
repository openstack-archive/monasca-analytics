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

from test.util_for_testing import MonanasTestCase


class TestMonascaAggregateLDP(MonanasTestCase):

    def setUp(self):
        super(TestMonascaAggregateLDP, self).setUp()
        self.all_metrics = [
            gen_metric("nb_cores", 1.2, 0, "h1"),
            gen_metric("nb_cores", 2.0, 1, "h1"),
            gen_metric("idl_perc", 0.2, 0, "h1"),
            gen_metric("idl_perc", 0.8, 1, "h1"),
        ]

    def tearDown(self):
        super(TestMonascaAggregateLDP, self).tearDown()
