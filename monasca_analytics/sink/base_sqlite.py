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

import abc
import logging
import six
import sqlite3
import time

import cPickle

from monasca_analytics.sink import base


DB_NAME_DEFAULT = "sqlite_sink.db"
logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseSQLiteSink(base.BaseSink):
    """Base class for SQLite sink to be extended by concrete implementations"""

    def __init__(self, _id, _config):
        super(BaseSQLiteSink, self).__init__(_id, _config)
        self.db_name = self._get_db_name(_config)
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(self._rdds_table_create_query())
            c.execute('''CREATE TABLE IF NOT EXISTS smls
                (timestamp INTEGER, voter_id TEXT, sml BLOB)''')
            conn.commit()

    def _get_db_name(self, _config):
        if "db_name" in _config:
            return _config["db_name"]
        return DB_NAME_DEFAULT

    def sink_dstream(self, dstream):
        dstream.foreachRDD(self._persist)

    def _persist(self, _, rdd):
        rdd_entries = rdd.collect()
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            for rdd_entry in rdd_entries:
                query = self._rdd_insert_query(rdd_entry)
                c.execute(query)
            conn.commit()

    def sink_ml(self, voter_id, matrix):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            timestamp = time.time()
            blob_matrix = cPickle.dumps(matrix, cPickle.HIGHEST_PROTOCOL)
            c.execute(
                'INSERT INTO smls (timestamp, voter_id, sml) VALUES(?, ?, ?);',
                [timestamp, voter_id, sqlite3.Binary(blob_matrix)])
            conn.commit()

    @abc.abstractmethod
    def _rdds_table_create_query(self):
        pass

    @abc.abstractmethod
    def _rdd_insert_query(self, rdd_json):
        pass
