#!/usr/bin/env python

import schema

import main.sink.base_sqlite as base


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
        return schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
            schema.Optional("db_name"): schema.And(
                basestring, lambda i: not any(c.isspace() for c in i)),
        }).validate(_config)
