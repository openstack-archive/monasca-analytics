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

import os.path as path
import re

import voluptuous

from monasca_analytics.config import const
from monasca_analytics.util import common_util as cu


def AvailableSink(msg=None):

    available_sink_classes = cu.get_available_classes(const.SINKS)[const.SINKS]
    available_sink_names = [Clazz.__name__ for Clazz in available_sink_classes]

    def f(v):
        if str(v) in available_sink_names:
            return str(v)
        else:
            raise voluptuous.Invalid(msg or ("Invalid Sink Name: " + str(v)))
    return f


def NoSpaceCharacter(msg=None):
    def f(v):
        if not any(c.isspace() for c in str(v)):
            return str(v)
        else:
            raise voluptuous.Invalid(msg or (
                "White space not allowed in: " + str(v)))
    return f


def ExistingPath(msg=None):
    def f(v):
        if path.exists(path.expanduser(str(v))) or\
                path.exists(path.dirname(path.expanduser(str(v)))):
            return str(v)
        else:
            raise voluptuous.Invalid(msg or (
                "Path does not exist: " + str(v)))
    return f


def NumericString(msg=None):
    def f(v):
        if re.match("[0-9]+", str(v)):
            return str(v)
        else:
            raise voluptuous.Invalid(msg or (
                "string does not represent a number"))
    return f


def ValidMarkovGraph(msg=None):
    def f(v):
        if len(str(v).split(":")) == 2 and str(v).split(":")[1] in\
                ["host", "web_service", "switch"]:
            return str(v)
        else:
            raise voluptuous.Invalid(msg or (
                "Key should be of the form 'anything:host' "
                "where 'host' can be replaced "
                "by 'web_service' or 'switch'."))
    return f


def NotEmptyArray(msg=None):
    def f(v):
        if len(v) > 0:
            return v
        else:
            raise voluptuous.Invalid(msg or ("empty array: " + str(v)))
    return f
