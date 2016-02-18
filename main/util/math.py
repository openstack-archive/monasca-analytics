#!/usr/bin/env python

import bisect


def interpolate_1d(table, value):
    """Return the interpolated result using the table for the passed value.

    :param table: list[(int, float)] -- a list where keys are numbers
    :param value: float | int -- the value we want to compute the result from.
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
