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
import math
import voluptuous

import monasca_analytics.banana.typeck.type_util as type_util
import monasca_analytics.component.params as params

import monasca_analytics.ldp.base as bt
import monasca_analytics.ldp.monasca.helpers as helpers
import monasca_analytics.util.spark_func as fn
from monasca_analytics.util import validation_utils as vu

logger = logging.getLogger(__name__)


# FIXME: This code is inaccurate because values on "edge" of the RDD
# FIXME: have a computed derivative with less precision than others.
# FIXME: The base idea would be to use the sliding window capability
# FIXME: to compute the derivative with the unbiased variant for all
# FIXME: values. However, we need a way to "know" how many derivative
# FIXME: calculation values needs to be skipped from one window to the
# FIXME: other.
# FIXME:
class MonascaDerivativeLDP(bt.BaseLDP):
    """Monasca derivative live data processor"""

    def __init__(self, _id, _config):
        super(MonascaDerivativeLDP, self).__init__(_id, _config)
        self._period = _config["period"]

    @staticmethod
    def validate_config(_config):
        monasca_der_schema = voluptuous.Schema({
            "module": voluptuous.And(basestring, vu.NoSpaceCharacter()),
            # Derivative period in multiple of batch interval
            "period": voluptuous.And(
                voluptuous.Or(float, int),
                lambda i: i >= 0 and math.floor(i) == math.ceil(i))
        }, required=True)
        return monasca_der_schema(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": MonascaDerivativeLDP.__name__,
            "period": 1
        }

    @staticmethod
    def get_params():
        return [
            params.ParamDescriptor('period', type_util.Number(), 1)
        ]

    def map_dstream(self, dstream):
        """
        Map the given DStream into a new DStream where metrics
        are replaced with their derivative.

        :type dstream: pyspark.streaming.DStream
        :param dstream: DStream
        :return: Returns the stream of derivative.
        """
        period = self._period
        return dstream.map(fn.from_json) \
            .window(period, period) \
            .map(lambda m: ((frozenset(
                m["metric"]["dimensions"].items()),
                m["metric"]["name"]),
                m)) \
            .groupByKey() \
            .flatMapValues(lambda metric: MonascaDerivativeLDP.derivative(
                metric,
            )) \
            .map(lambda x: x[1])

    @staticmethod
    def derivative(metric_values):
        """
        Compute the derivative of the given function.

        :type metric_values: pyspark.resultiterable.ResultIterable[dict]
        :param metric_values: The list of metric_values
        :return: Returns the derivative of the provided metric.
        """
        if len(metric_values.data) < 2:
            return []

        metric_name = metric_values.data[0]["metric"]["name"] + "_derivative"
        meta = metric_values.data[0]["meta"]
        dims = metric_values.data[0]["metric"]["dimensions"]
        # All values
        timestamps = map(lambda m: m["metric"]["timestamp"], metric_values)
        all_values = map(lambda m: m["metric"]["value"], metric_values)
        # Sort values
        all_values = [y for (_, y) in
                      sorted(zip(timestamps, all_values), key=lambda x: x[0])]
        timestamps = sorted(timestamps)
        # Remove duplicates
        last_timestamp = timestamps[0]
        tmp_all_values = [all_values[0]]
        tmp_timestamps = [last_timestamp]
        for index in xrange(1, len(timestamps)):
            if timestamps[index] == last_timestamp:
                continue
            else:
                last_timestamp = timestamps[index]
                tmp_all_values.append(all_values[index])
                tmp_timestamps.append(last_timestamp)
        all_values = tmp_all_values
        timestamps = tmp_timestamps

        if len(all_values) < 2:
            return []

        # Filter all values that have the same timestamp
        n = len(all_values) - 1
        new_values = [
            float(all_values[1] - all_values[0]) /
            float(timestamps[1] - timestamps[0])
        ]
        for index in xrange(1, n):
            new_values.append(
                float(all_values[index + 1] - all_values[index - 1]) /
                float(timestamps[index + 1] - timestamps[index - 1])
            )
        new_values.append(
            float(all_values[n] - all_values[n - 1]) /
            float(timestamps[n] - timestamps[n - 1])
        )
        new_metrics = [
            helpers.create_agg_metric(
                metric_name,
                meta,
                dims,
                tmst,
                val
            ) for val, tmst in zip(new_values, timestamps)
        ]
        return new_metrics
