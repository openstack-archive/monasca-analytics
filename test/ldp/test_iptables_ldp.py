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

from monasca_analytics.ldp import iptables_ldp
from test.mocks import classifier_mock
from test.util_for_testing import MonanasTestCase


class TestIptablesLDP(MonanasTestCase):

    def setUp(self):
        super(TestIptablesLDP, self).setUp()
        self.rdd_entry = [{
            "ctime": "Mon Apr 11 19:59:12 2016",
            "event": {
                "msg": "OUTPUT -p icmp --icmp-type echo-request -j ACCEPT",
                "id": "1"
            }
        }, {
            "ctime": "Mon Apr 11 19:59:12 2016",
            "event": {
                "msg": "OUTPUT -o eth0 -p tcp --sport 80 -j ACCEPT",
                "id": "1"
            }
        }]
        self.raw_events = [x["event"] for x in self.rdd_entry]
        self.ip_ldp = iptables_ldp.IptablesLDP("fake_id",
                                               {"module": "fake_config"})

    def tearDown(self):
        super(TestIptablesLDP, self).tearDown()

    def assert_anomalous_events(self, events, anomalous=True):
        expected_events = self.raw_events
        for exv in expected_events:
            exv["anomalous"] = anomalous
        self.assertEqual(expected_events, events)

    def test_detect_anomalies_no_features(self):
        self.clf = classifier_mock.MockClassifier(False)
        self.ip_ldp.set_voter_output(self.clf)
        ret = self.ip_ldp._detect_anomalies(self.rdd_entry,
                                            self.ip_ldp._data)
        self.assertEqual(self.raw_events, ret)

    def test_detect_anomalies_no_classifier(self):
        self.clf = classifier_mock.MockClassifier(False)
        self.ip_ldp.set_feature_list(["ssh", "ip", "http", "ping"])
        ret = self.ip_ldp._detect_anomalies(self.rdd_entry,
                                            self.ip_ldp._data)
        self.assertEqual(self.raw_events, ret)

    def test_detect_anomalies_non_anomalous(self):
        self.clf = classifier_mock.MockClassifier(False)
        self.ip_ldp.set_feature_list(["ssh", "ip", "http", "ping"])
        self.ip_ldp.set_voter_output(self.clf)
        ret = self.ip_ldp._detect_anomalies(self.rdd_entry,
                                            self.ip_ldp._data)
        self.assert_anomalous_events(ret, False)

    def test_detect_anomalies_anomalous(self):
        self.clf = classifier_mock.MockClassifier(True)
        self.ip_ldp.set_feature_list(["ssh", "ip", "http", "ping"])
        self.ip_ldp.set_voter_output(self.clf)
        ret = self.ip_ldp._detect_anomalies(self.rdd_entry,
                                            self.ip_ldp._data)
        self.assert_anomalous_events(ret, True)
