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
import voluptuous

import monasca_analytics.banana.typeck.type_util as type_util
import monasca_analytics.component.params as params

import monasca_analytics.ldp.base as bt
import monasca_analytics.ldp.monasca.helpers as helpers
import monasca_analytics.util.spark_func as fn
from monasca_analytics.util import validation_utils as vu

logger = logging.getLogger(__name__)


class MonascaAggregateLDP(bt.BaseLDP):
    """Monasca aggregator live data processor"""

    def __init__(self, _id, _config):
        super(MonascaAggregateLDP, self).__init__(_id, _config)
        self._aggregation_period = _config["period"]
        self._reducer_func = MonascaAggregateLDP.select_reducer(_config)
        self._suffix = "_" + _config["func"]

    @staticmethod
    def validate_config(_config):
        monasca_ag_schema = voluptuous.Schema({
            "module": voluptuous.And(basestring, vu.NoSpaceCharacter()),
            "period": voluptuous.Or(float, int),
            "func": voluptuous.Or(
                "avg",
                "max",
                "sum",
                "min",
                "cnt"
            )
        }, required=True)
        return monasca_ag_schema(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": MonascaAggregateLDP.__name__,
            "period": 60.0 * 60.0,
            "func": "avg"
        }

    @staticmethod
    def get_params():
        return [
            params.ParamDescriptor('period', type_util.Number(), 60 * 60),
            params.ParamDescriptor(
                'func',
                type_util.Enum(['avg', 'max', 'sum', 'min', 'cnt']),
                'avg'
            )
        ]

    def map_dstream(self, dstream):
        """
        Map the given DStream into a new DStream where metrics
        have been aggregated by name.

        :type dstream: pyspark.streaming.DStream
        :param dstream: DStream
        :return: Returns the stream of aggregated metrics
        """
        red = self._reducer_func
        suf = self._suffix
        agg_period = self._aggregation_period
        # TODO(Joan): Add a filter to only aggregate some metrics
        # TODO(Joan): or particular dimensions
        return dstream.map(fn.from_json) \
            .window(agg_period, agg_period) \
            .map(lambda metric: (metric["metric"]["name"], metric)) \
            .groupByKey() \
            .flatMapValues(lambda metrics: MonascaAggregateLDP.aggregate(
                metrics,
                red,
                suf
            ))\
            .map(lambda metric_and_name: metric_and_name[1])

    @staticmethod
    def aggregate(all_metrics, reducer, suffix):
        """
        Aggregate values produced by different providers together.
        The metric name is assumed to be the same for all providers.

        :type all_metrics: list[dict]
        :param all_metrics: Values to aggregate mapping to a specific
                            metric name.
        :type reducer: ((float, float) -> float,
            (float, float, float) -> float)
        :param reducer: Combine the metrics values together
        :type suffix: str
        :param suffix: Suffix to append to the metric name in its combined form
        """
        # Collect metric separately
        separated_metrics = {}  # type: dict[frozenset, list[dict]]
        for el in all_metrics:
            key = frozenset(el["metric"]["dimensions"].items())
            if key not in separated_metrics:
                separated_metrics[key] = [el]
            else:
                separated_metrics[key].append(el)

        # Collect all dimensions
        dims = {}
        for metric_dims in separated_metrics.keys():
            for prop, val in dict(metric_dims).iteritems():
                if prop in dims:
                    dims[prop].add(val)
                else:
                    dims[prop] = set(val)

        # Sort each metric
        for _, metric in separated_metrics.iteritems():
            metric.sort(key=lambda v: v["metric"]["timestamp"])

        separated_metrics = sorted(separated_metrics.values(), key=len)
        separated_metrics.reverse()

        # Compute the new values
        new_values = []
        all_timestamps = map(
            lambda l: map(
                lambda x: x["metric"]["timestamp"], l),
            separated_metrics)
        metric_count = len(separated_metrics)
        for index in xrange(0, len(separated_metrics[0])):
            new_value = reducer[0](
                separated_metrics[0][index]["metric"]["value"],
                metric_count)
            new_timestamp = separated_metrics[0][index]["metric"]["timestamp"]
            for metric_index in xrange(1, metric_count):
                new_value = reducer[1](new_value, helpers.interpolate(
                    new_timestamp,
                    separated_metrics[metric_index],
                    all_timestamps[metric_index]
                ), metric_count)
            new_values.append((new_timestamp, new_value))

        # Aggregate the other details:
        metric_name = separated_metrics[0][0]["metric"]["name"] + suffix
        meta = separated_metrics[0][0]["meta"]
        new_metrics = [
            helpers.create_agg_metric(
                metric_name,
                meta,
                dims,
                val[0],
                val[1]
            ) for val in new_values
        ]
        return new_metrics

    @staticmethod
    def select_reducer(_config):
        return {
            "avg": (
                lambda m, cnt: m / cnt,
                lambda acc, m, cnt: m / cnt + acc,
            ),
            "max": (
                lambda m, cnt: m,
                lambda acc, m, cnt: max(m, acc),
            ),
            "sum": (
                lambda m, cnt: m,
                lambda acc, m, cnt: m + acc,
            ),
            "min": (
                lambda m, cnt: m,
                lambda acc, m, cnt: min(m, acc),
            ),
            "cnt": (
                lambda m, cnt: m,
                lambda acc, m, cnt: cnt,
            ),
        }[_config["func"]]
