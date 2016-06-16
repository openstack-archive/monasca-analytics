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

import logging

from pyspark.streaming import kafka
import schema

from monasca_analytics.source import base

logger = logging.getLogger(__name__)


class KafkaSource(base.BaseSource):
    """A Kafka source implementation that consumes data from a Kafka queue."""

    @staticmethod
    def validate_config(_config):
        source_schema = schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
            "params": {
                "zk_host": schema.And(basestring,
                                      lambda i: not any(c.isspace()
                                                        for c in i)),
                "zk_port": int,
                "group_id": schema.And(basestring,
                                       lambda i: not any(c.isspace()
                                                         for c in i)),
                "topics": {
                    schema.And(basestring, lambda i: not any(c.isspace()
                                                             for c in i)):
                    schema.And(int, lambda p: p > 0)
                }
            }
        })
        return source_schema.validate(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": KafkaSource.__name__,
            "params": {
                "zk_host": "localhost",
                "zk_port": 2181,
                "group_id": "my_group_id",
                "topics": {
                    "my_topic": 1
                }
            }
        }

    def create_dstream(self, ssc):
        """Dstream creation

        The _dstream object is created before this source is bound
        to the consumers. It uses a KafkaUtils.createStream, to read data from
        the Kafka queue that was defined in the configuration.

        :type ssc: pyspark.streaming.StreamingContext
        :param ssc: Spark Streaming Context
        """
        return kafka.KafkaUtils.createStream(
            ssc,
            "{0}:{1}".format(
                self._config["params"]["zk_host"],
                self._config["params"]["zk_port"]),
            self._config["params"]["group_id"],
            self._config["params"]["topics"])

    def terminate_source(self):
        pass

    def get_feature_list(self):
        raise NotImplementedError("This method needs to be implemented")
