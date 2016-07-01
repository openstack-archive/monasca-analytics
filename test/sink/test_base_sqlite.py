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
import sqlite3
import unittest

import cPickle
import numpy as np
import voluptuous

from monasca_analytics.sink import base_sqlite as bsql
from test.mocks import spark_mocks


class BaseSQLiteSinkDummyExtension(bsql.BaseSQLiteSink):

    def _rdds_table_create_query(self):
        return """CREATE TABLE IF NOT EXISTS rdds
            (fake_col1 TEXT, fake_col2 TEXT)"""

    def _rdd_insert_query(self, rdd_json):
        return ('INSERT INTO rdds VALUES("' + rdd_json["one"] +
                '", "' + rdd_json["two"] + '")')

    @staticmethod
    def get_default_config():
        return {
            "module": BaseSQLiteSinkDummyExtension.__name__,
            "params": {
                "db_name": "sqlite_sink.db"
            }
        }

    @staticmethod
    def validate_config(_config):
        base_schema = voluptuous.Schema({
            "module": voluptuous.And(
                basestring, lambda i: not any(c.isspace() for c in i)),
            voluptuous.Optional("db_name"): voluptuous.And(
                basestring, lambda i: not any(c.isspace() for c in i)),
        }, required=True)
        return base_schema(_config)


class TestSQLiteSink(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self._valid_config = {"module": "BaseSQLiteSinkDummyExtension"}
        self.snk = BaseSQLiteSinkDummyExtension("fake_id", self._valid_config)

    def get_rdd_mock(self):
        rdd = spark_mocks.MockRDD(None, None, None)
        rdd_entries = [{"one": "row1col1", "two": "row1col2"},
                       {"one": "row2col1", "two": "row2col2"},
                       {"one": "row3col1", "two": "row3col2"}]
        rdd.set_rdd_entries(rdd_entries)
        return rdd

    def assert_rdd_written_to_db(self, rdd):
        with sqlite3.connect("sqlite_sink.db") as conn:
            c = conn.cursor()
            for row in c.execute('SELECT * FROM rdds'):
                if self._find_row_in_rdd(row, rdd):
                    return
        self.fail("Did not find rdd in database")

    def _find_row_in_rdd(self, row, rdd):
        for rdd_entry in rdd._rdd_entries:
            if rdd_entry["one"] == row[0] and rdd_entry["two"] == row[1]:
                return True
        return False

    def assert_sml_written_to_db(self, sml, voter_id):
        with sqlite3.connect("sqlite_sink.db") as conn:
            c = conn.cursor()
            c.execute('SELECT sml FROM smls WHERE voter_id = "' +
                      voter_id + '"')
            fetched_sml = c.fetchone()
            fetched_sml = cPickle.loads(str(fetched_sml[0]))
            self.assertEqual(len(sml), len(fetched_sml))
            self.assertTrue((sml == fetched_sml).all())

    def test_validate_valid_config_no_dbname(self):
        conf = {"module": "BaseSQLiteSinkDummyExtension"}
        self.snk.validate_config(conf)

    def test_validate_valid_config_with_dbname(self):
        conf = {"module": "BaseSQLiteSinkDummyExtension",
                "db_name": "mySQLite.db"}
        self.snk.validate_config(conf)

    def test_validate_config_no_module(self):
        conf = {"db_name": "mySQLite.db"}
        self.assertRaises(voluptuous.Invalid, self.snk.validate_config, conf)

    def test_validate_config_extra_param(self):
        conf = {"module": "BaseSQLiteSinkDummyExtension",
                "infiltrated": "I shouldn't be here"}
        self.assertRaises(voluptuous.Invalid, self.snk.validate_config, conf)

    def test_get_db_name(self):
        conf = {"db_name": "mySQLite.db"}
        db_name = self.snk._get_db_name(conf)
        self.assertEqual("mySQLite.db", db_name)

    def test_get_db_name_default(self):
        conf = {"module": "BaseSQLiteSinkDummyExtension"}
        db_name = self.snk._get_db_name(conf)
        self.assertEqual(bsql.DB_NAME_DEFAULT, db_name)

    def test_persist(self):
        rdd = self.get_rdd_mock()
        self.snk._persist(None, rdd)
        self.assert_rdd_written_to_db(rdd)

    def test_sink_ml_array(self):
        sml = np.array([[1, 2, 3], ["a", "b", "c"], [.1, .5, .9]])
        self.snk.sink_ml("vot1", sml)
        self.assert_sml_written_to_db(sml, "vot1")

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        os.remove("sqlite_sink.db")

if __name__ == "__main__":
    unittest.main()
