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

import bisect
import time


def interpolate(timestamp, metric_values, metric_timestamps):
    """
    :type timestamp: int
    :param timestamp: Timestamp at witch we want to interpolate or extrapolate
                      the metric value
    :type metric_values: list[dict]
    :param metric_values: List of metrics
    :type metric_timestamps: list[int]
    :param metric_timestamps: List of timestamp for the given metric.
    :rtype: float
    :return: Returns the interpolated value
    """
    insertion_pos = bisect.bisect_left(metric_timestamps, timestamp)
    # Edge cases:
    if insertion_pos == 0:
        return metric_values[0]["metric"]["value"]
    if insertion_pos == len(metric_timestamps) - 1:
        return metric_values[len(metric_timestamps) - 1]["metric"]["value"]
    if metric_timestamps[insertion_pos] == timestamp:
        return metric_values[insertion_pos]["metric"]["value"]
    # General case:
    lo = metric_timestamps[insertion_pos - 1]
    hi = metric_timestamps[insertion_pos]
    dt = hi - lo
    return metric_values[insertion_pos - 1]["metric"]["value"] *\
        (timestamp - lo) / dt + \
        metric_values[insertion_pos]["metric"]["value"] *\
        (hi - timestamp) / dt


def create_agg_metric(metric_name, meta, dimensions, timestamp, value):
    return {
        "metric": {
            "name": metric_name,
            "dimensions": dimensions,
            "timestamp": timestamp,
            "value": value
        },
        "meta": meta,
        "creation_time": int(time.time())
    }
