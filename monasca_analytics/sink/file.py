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
import os.path as path
import schema
import tempfile
import time

import monasca_analytics.sink.base as base


class FileSink(base.BaseSink):
    """Sink that prints the dstream to a file in the driver

    This sink is for development **only**.
    """

    def __init__(self, _id, _config):
        super(FileSink, self).__init__(_id, _config)
        if "params" in _config:
            _path = path.expanduser(_config["params"]["path"])
            if path.isdir(_path):
                _path = path.join(_path, time.time() + '.log')
            self._file_path = _path
        else:
            self._file_path = tempfile.NamedTemporaryFile().name

    def sink_dstream(self, dstream):
        """
        Sink the provided DStream into a file.

        :type dstream: pyspark.streaming.DStream
        :param dstream: DStream to sink
        """
        _file_name = self._file_path

        def write_output(rdd):
            _file = open(_file_name, 'a+')
            for rdd_entry in rdd.collect():
                _file.write(json.dumps(rdd_entry, indent=4))

        dstream.foreachRDD(lambda _, rdd: write_output(rdd))

    def sink_ml(self, voter_id, matrix):
        pass

    @staticmethod
    def get_default_config():
        return {
            "module": FileSink.__name__,
            "params": {
                "path": None
            }
        }

    @staticmethod
    def validate_config(_config):
        return schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
            schema.Optional("params"): {
                "path": schema.And(
                    basestring,
                    lambda i: path.exists(path.expanduser(i)) or
                    path.exists(path.dirname(path.expanduser(i)))
                )
            }
        }).validate(_config)
