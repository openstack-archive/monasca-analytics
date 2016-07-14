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
import time

import kafka

import monasca_analytics.banana.typeck.type_util as type_util
import monasca_analytics.component.params as params
from monasca_analytics.sink import base
import monasca_analytics.sink.sink_config_validator as validator


class KafkaSink(base.BaseSink):
    """A Kafka sink for dstream"""

    def __init__(self, _id, _config):
        self._topic = None
        self._producer = None
        super(KafkaSink, self).__init__(_id, _config)
        self._host = _config["host"]
        self._port = int(_config["port"])
        self._topic = _config["topic"]

    def sink_dstream(self, dstream):
        if self._producer is None:
            self._producer = kafka.KafkaProducer(
                bootstrap_servers="{0}:{1}".format(self._host, self._port))
        dstream.foreachRDD(self._persist)

    def _persist(self, _, rdd):
        rdd_entries = rdd.collect()

        for rdd_entry in rdd_entries:
            self._producer.send(self._topic,
                                json.dumps(rdd_entry))
            self._producer.flush()

    def sink_ml(self, voter_id, matrix):
        output = dict(
            id=voter_id,
            matrix=matrix,
            timestamp=time.time()
        )
        self._producer.send(self._topic,
                            json.dumps(output))

    @staticmethod
    def validate_config(_config):
        validator.validate_kafka_sink_config(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": KafkaSink.__name__,
            "host": "localhost",
            "port": 9092,
            "topic": "transformed_alerts"
        }

    @staticmethod
    def get_params():
        return [
            params.ParamDescriptor('host', type_util.String(), 'localhost'),
            params.ParamDescriptor('port', type_util.Number(), 9092),
            params.ParamDescriptor('topic', type_util.String(),
                                   'transformed_alerts')
        ]
