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

from monasca_analytics.ldp import iptables_ldp
from test.mocks import classifier_mock


class TestIptablesLDP(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        self.setup_logging()
        self.rdd_entry = {
            "ctime": "Mon Apr 11 19:59:12 2016",
            "events": [
                {
                    "msg": "OUTPUT -p icmp --icmp-type echo-request -j ACCEPT",
                    "id": "1"},
                {
                    "msg": "OUTPUT -o eth0 -p tcp --sport 80 -j ACCEPT",
                    "id": "1"}
            ]
        }
        self.ip_ldp = iptables_ldp.IptablesLDP("fake_id",
                                               {"module": "fake_config"})

    def tearDown(self):
        pass

    def assert_anomalous_events(self, events, anomalous=True):
        expected_events = self.rdd_entry["events"]
        for exv in expected_events:
            exv["ctime"] = self.rdd_entry["ctime"]
            exv["anomalous"] = anomalous
        self.assertEqual(expected_events, events)

    def test_detect_anomalies_no_features(self):
        self.clf = classifier_mock.MockClassifier(False)
        self.ip_ldp.set_voter_output(self.clf)
        ret = self.ip_ldp._detect_anomalies(json.dumps(self.rdd_entry),
                                            self.ip_ldp._data)
        self.assertEqual(self.rdd_entry["events"], ret)

    def test_detect_anomalies_no_classifier(self):
        self.clf = classifier_mock.MockClassifier(False)
        self.ip_ldp.set_feature_list(["ssh", "ip", "http", "ping"])
        ret = self.ip_ldp._detect_anomalies(json.dumps(self.rdd_entry),
                                            self.ip_ldp._data)
        self.assertEqual(self.rdd_entry["events"], ret)

    def test_detect_anomalies_non_anomalous(self):
        self.clf = classifier_mock.MockClassifier(False)
        self.ip_ldp.set_feature_list(["ssh", "ip", "http", "ping"])
        self.ip_ldp.set_voter_output(self.clf)
        ret = self.ip_ldp._detect_anomalies(json.dumps(self.rdd_entry),
                                            self.ip_ldp._data)
        self.assert_anomalous_events(ret, False)

    def test_detect_anomalies_anomalous(self):
        self.clf = classifier_mock.MockClassifier(True)
        self.ip_ldp.set_feature_list(["ssh", "ip", "http", "ping"])
        self.ip_ldp.set_voter_output(self.clf)
        ret = self.ip_ldp._detect_anomalies(json.dumps(self.rdd_entry),
                                            self.ip_ldp._data)
        self.assert_anomalous_events(ret, True)
