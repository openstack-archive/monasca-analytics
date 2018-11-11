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

import six
import voluptuous

import monasca_analytics.ldp.base as bt
import monasca_analytics.util.spark_func as fn
import monasca_analytics.util.validation_utils as vu


logger = logging.getLogger(__name__)


class CloudCausalityLDP(bt.BaseLDP):
    """A causality live data processor"""

    @staticmethod
    def validate_config(_config):
        cloud_causality_schema = voluptuous.Schema({
            "module": voluptuous.And(six.string_types[0],
                                     vu.NoSpaceCharacter())
        }, required=True)
        return cloud_causality_schema(_config)

    @staticmethod
    def get_default_config():
        return {"module": CloudCausalityLDP.__name__}

    @staticmethod
    def get_params():
        return []

    def map_dstream(self, dstream):
        """Executes _aggregate for each RDD in the dstream

        :type dstream: pyspark.streaming.DStream
        :param dstream: DStream created by the source.
        """
        data = self._data
        return dstream.map(fn.from_json)\
            .map(lambda x: (x['ctime'], x))\
            .groupByKey()\
            .flatMap(lambda r: CloudCausalityLDP._aggregate(r[1], data))

    @staticmethod
    def _aggregate(rdd_entry, data):
        new_entries = []
        features = data["features"]
        matrix = data["matrix"]

        if features is None or matrix is None:
            return rdd_entry

        for event in rdd_entry:
            causes = []

            try:
                cause = features.index(event["event"]["id"])
                for other_event in rdd_entry:
                    if other_event["event"]["id"] != event["event"]["id"]:
                        try:
                            caused = features.index(other_event["event"]["id"])

                            if matrix[caused][cause]:
                                causes.append(other_event["event"]["id"])
                        except ValueError:
                            pass
            except ValueError:
                pass

            event["__monanas__"] = dict(causes=causes)
            new_entries.append(event)

        return new_entries
