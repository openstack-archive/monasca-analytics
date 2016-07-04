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

import voluptuous

import monasca_analytics.sink.base_sqlite as base
from monasca_analytics.util import validation_utils as vu


class IptablesSQLiteSink(base.BaseSQLiteSink):
    """IPTables SQLite Sink implementation."""

    def _rdds_table_create_query(self):
        return """CREATE TABLE IF NOT EXISTS rdds
            (msg TEXT, anomalous TEXT, msg_id TEXT, ctime TEXT)"""

    def _rdd_insert_query(self, rdd_json):
        return ('INSERT INTO rdds VALUES("' + str(rdd_json["msg"]) + '", "' +
                str(rdd_json["anomalous"]) + '", "' + str(rdd_json["id"]) +
                '", "' + str(rdd_json["ctime"]) + '")')

    @staticmethod
    def get_default_config():
        return {
            "module": IptablesSQLiteSink.__name__,
            "params": {
                "db_name": "sqlite_sink.db"
            }
        }

    @staticmethod
    def validate_config(_config):
        iptables_sql_schema = voluptuous.Schema({
            "module": voluptuous.And(basestring, vu.NoSpaceCharacter()),
            voluptuous.Optional("db_name"): voluptuous.And(
                basestring, vu.NoSpaceCharacter()),
        }, required=True)
        return iptables_sql_schema(_config)
