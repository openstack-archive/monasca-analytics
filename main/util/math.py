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

import bisect


def interpolate_1d(table, value):
    """Return the interpolated result using the table for the passed value.

    :type table: list[(int, float)]
    :param table: a list where keys are numbers
    :type value: float | int
    :param value: the value we want to compute the result from.
    """
    table.sort(key=lambda fn: fn[0])
    keys = [fv[0] for fv in table]
    index = bisect.bisect(keys, value)
    if index == 0:
        return table[index][1]
    elif index == len(table):
        return table[index - 1][1]
    else:
        lo = table[index - 1]
        hi = table[index]
        return (hi[1] - lo[1]) * (value - lo[0]) / (hi[0] - lo[0]) + lo[1]
