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

from monasca_analytics.sink import iptables_sqlite as ipt_snk


class TestIptablesSQLiteSink(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self._valid_config = {"module": "IptablesSQLiteSink"}
        self.snk = ipt_snk.IptablesSQLiteSink("fake_id", self._valid_config)

    def test_rdds_table_create_query(self):
        query = self.snk._rdds_table_create_query()
        self.assertEqual("""CREATE TABLE IF NOT EXISTS rdds
            (msg TEXT, anomalous TEXT, msg_id TEXT, ctime TEXT)""", query)

    def test_rdd_insert_query_valid_rdd(self):
        rdd_entry = {
            "msg": "test message",
            "id": 1,
            "anomalous": True,
            "ctime": "t1"
        }
        query = self.snk._rdd_insert_query(rdd_entry)
        self.assertEqual(
            'INSERT INTO rdds VALUES("test message", "True", "1", "t1")',
            query)

    def test_rdd_insert_query_invalid_rdd(self):
        rdd_entry = {
            "msg": "test message",
            "anomalous": True,
            "ctime": "t1"
        }
        self.assertRaises(KeyError, self.snk._rdd_insert_query, rdd_entry)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        os.remove("sqlite_sink.db")

if __name__ == "__main__":
    unittest.main()
