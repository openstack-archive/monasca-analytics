#!/usr/bin/env python

import random

from main.util import math


class ProbCheck(object):
    """Function object to randomly return True or False with probability

    This function object randomly returns true or false
    with a chance of success that can optionally vary
    given the hour of the day.
    """

    def __init__(self, prob):
        """Create a ProbCheck, or change stat if the prob check is passed.

        :param prob: dict[int, float] | float -- a probability value or a
        dictionary where the key is the hour of the day and the value
        is the probability associated with it.
        """
        if isinstance(prob, dict):
            self._prob = prob.items()
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
