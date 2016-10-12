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
import monasca_analytics.parsing.api as parsing
import monasca_analytics.util.spark_func as fn
from monasca_analytics.util import validation_utils as vu

logger = logging.getLogger(__name__)


class MonascaCombineLDP(bt.BaseLDP):
    """Monasca combiner live data processor"""

    def __init__(self, _id, _config):
        super(MonascaCombineLDP, self).__init__(_id, _config)
        logger.debug(_config["bindings"])
        logger.debug(_config["lambda"])
        self._combine_function = parsing.create_fn_with_config(
            env=_config["bindings"],
            expr_string=_config["lambda"]
        )
        self._combine_period = _config["period"]
        self._combine_metric_name = _config["metric"]
        self._metrics_of_interest = _config["bindings"].values()

    def map_dstream(self, dstream):
        """
        Map the given DStream into a new DStream where the specified metrics
        have been combined together.

        :type dstream: pyspark.streaming.DStream
        :param dstream: DStream
        :return: Returns the stream of combined metrics
        """
        combine_fn = self._combine_function
        metric_names = self._metrics_of_interest
        nb_metrics = len(metric_names)
        metric_name = self._combine_metric_name
        return dstream.map(fn.from_json)\
            .window(self._combine_period, self._combine_period)\
            .filter(lambda x: x["metric"]["name"] in metric_names and
                    x["metric"]["value"] is not None) \
            .map(lambda x: (frozenset(x["metric"]["dimensions"]), x))\
            .groupByKey()\
            .flatMapValues(lambda metrics: MonascaCombineLDP.combine(
                metrics,
                combine_fn,
                metric_name,
                nb_metrics
            ))\
            .map(lambda x: x[1])

    @staticmethod
    def combine(all_metrics, combine_fn, combine_metric_name, nb_of_metrics):
        """
        Combine the given metrics of this RDD into one.

        :type all_metrics: pyspark.resultiterable.ResultIterable
        :param all_metrics: List containing the metrics.
        :param combine_fn: Combiner.
        :type combine_metric_name: str
        :param combine_metric_name: Name of the new metric
        :type nb_of_metrics: int
        :param nb_of_metrics: The number of metrics expected
        """
        # Separate metrics based on name
        separated_metrics = {}  # type: dict[str, list[dict]]
        dims = None
        for el in all_metrics:
            key = el["metric"]["name"]
            if dims is None:
                dims = el["metric"]["dimensions"]
            if key not in separated_metrics:
                separated_metrics[key] = [el]
            else:
                separated_metrics[key].append(el)

        if len(separated_metrics.keys()) != nb_of_metrics:
            return []

        separated_metrics = sorted(list(separated_metrics.iteritems()),
                                   key=lambda x: len(x[1]))
        separated_metrics = separated_metrics  # type: list[(str, list[dict])]

        # Sort each metric
        for metric in separated_metrics:
            metric[1].sort(key=lambda v: v["metric"]["timestamp"])

        temp_values = []
        all_timestamp = map(
            lambda l: map(
                lambda x: x["metric"]["timestamp"], l[1]),
            separated_metrics)
        for index in range(0, len(separated_metrics[0][1])):
            current_env = {
                separated_metrics[0][0]:
                    separated_metrics[0][1][index]["metric"]["value"]
            }
            timestamp = all_timestamp[0][index]
            for metric_index in range(1, len(separated_metrics)):
                metric_prop = separated_metrics[metric_index]
                metric_name = metric_prop[0]
                current_env[metric_name] = helpers.interpolate(
                    timestamp,
                    metric_prop[1],
                    all_timestamp[metric_index]
                )
            temp_values.append(current_env)

        new_values = map(combine_fn, temp_values)

        new_metrics = [
            helpers.create_agg_metric(
                combine_metric_name,
                {},
                dims,
                tsmp,
                val
            ) for val, tsmp in zip(new_values, all_timestamp[0])
        ]
        return new_metrics

    @staticmethod
    def validate_config(_config):
        monasca_comb_schema = voluptuous.Schema({
            "module": voluptuous.And(basestring, vu.NoSpaceCharacter()),
            "metric": basestring,
            "period": voluptuous.And(
                voluptuous.Or(float, int),
                lambda i: i >= 0 and math.floor(i) == math.ceil(i)),
            "lambda": basestring,
            "bindings": {
                basestring: voluptuous.Or(
                    "apache.net.kbytes_sec",
                    "apache.net.requests_sec",
                    "apache.performance.cpu_load_perc",
                    "cpu.idle_perc",
                    "cpu.stolen_perc",
                    "cpu.system_perc",
                    "cpu.total_logical_cores",
                    "cpu.user_perc",
                    "cpu.wait_perc",
                    "disk.allocation",
                    "disk.inode_used_perc",
                    "disk.space_used_perc",
                    "disk.total_space_mb",
                    "disk.total_used_space_mb",
                    "host_alive_status",
                    "io.read_kbytes_sec",
                    "io.read_req_sec",
                    "io.write_time_sec",
                    "kafka.consumer_lag",
                    "load.avg_1_min",
                    "load.avg_5_min",
                    "mem.free_mb",
                    "mem.swap_free_mb",
                    "mem.swap_total_mb",
                    "mem.total_mb",
                    "mem.usable_mb",
                    "mem.used_cache",
                    "metrics-added-to-batch-counter[0]",
                    "mysql.innodb.buffer_pool_free",
                    "mysql.innodb.buffer_pool_used",
                    "mysql.innodb.data_reads",
                    "mysql.innodb.mutex_spin_rounds",
                    "mysql.performance.com_delete_multi",
                    "mysql.performance.com_insert",
                    "mysql.performance.com_insert_select",
                    "mysql.performance.com_select",
                    "mysql.performance.com_update",
                    "mysql.performance.created_tmp_disk_tables",
                    "mysql.performance.created_tmp_files",
                    "mysql.performance.open_files",
                    "mysql.performance.questions",
                    "mysql.performance.user_time",
                    "net.in_bytes_sec",
                    "net.in_errors_sec",
                    "net.in_packets_dropped_sec",
                    "net.in_packets_sec",
                    "net.out_bytes_sec",
                    "net.out_errors_sec",
                    "net.out_packets_dropped_sec",
                    "net.out_packets_sec",
                    "nova.vm.disk.total_allocated_gb",
                    "process.pid_count",
                    "raw-sql.time.max",
                    "vcpus",
                    "vm.cpu.utilization_perc",
                    "vm.host_alive_status",
                    "vm.mem.total_mb",
                    "zookeeper.out_bytes",
                    "zookeeper.outstanding_bytes"
                )
            }
        }, required=True)
        monasca_comb_schema(_config)
        # Checks the expression and the environment
        handle = parsing.validate_expression(_config["lambda"])
        parsing.validate_name_binding(handle,
                                      _config["bindings"])

    @staticmethod
    def get_default_config():
        return {
            "module": MonascaCombineLDP.__name__,
            "metric": "cpu.logical_cores_actives",
            "period": 1,
            "lambda": "a * b",
            "bindings": {
                "a": "cpu.idle_perc",
                "b": "cpu.total_logical_cores"
            }
        }

    @staticmethod
    def get_params():
        return [
            params.ParamDescriptor(
                'metric',
                type_util.String(),
                'cpu.logcal_cores_actives'
            ),
            params.ParamDescriptor(
                'period',
                type_util.Number(),
                1
            ),
            params.ParamDescriptor(
                'lambda',
                type_util.String(),
                'a * b'
            ),
            params.ParamDescriptor(
                'bindings',
                type_util.Any(),
                {'a': 'cpu.ilde_perc', 'b': 'cpu.total_logical_cores'}
            )
        ]
