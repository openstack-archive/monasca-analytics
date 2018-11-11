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

import random

from monasca_analytics.util import math


class ProbCheck(object):
    """Function object to randomly return True or False with probability

    This function object randomly returns true or false
    with a chance of success that can optionally vary
    given the hour of the day.
    """

    def __init__(self, prob):
        """Create a ProbCheck, or change stat if the prob check is passed.

        :type prob: dict[int, float] | float
        :param prob: a probability value or a dictionary where keys correspond
                     to the hour of the day and the value is the probability of
                     success associated with it.
        """
        if isinstance(prob, dict):
            self._prob = list(prob.items())
        else:
            self._prob = prob

    def __call__(self, hour_of_day):
        if isinstance(self._prob, list):
            p = math.interpolate_1d(self._prob, hour_of_day)
        else:
            p = self._prob
        return random.random() < p


class NoProbCheck(object):
    """When you don't want to have any prob check performed."""

    def __call__(self, *_):
        return True
