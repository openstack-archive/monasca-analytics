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

"""A list of functions for validating sink configs."""

import math
import voluptuous

from monasca_analytics.util import validation_utils as vu


def validate_kafka_sink_config(config):
    """Validates the KafkaSink configuration"""

    config_schema = voluptuous.Schema({
        "module": voluptuous.And(basestring, vu.AvailableSink()),
        "host": voluptuous.And(
            basestring, vu.NoSpaceCharacter()),
        "port": voluptuous.And(
            voluptuous.Or(float, int),
            lambda i: i >= 0 and math.floor(i) == math.ceil(i)),
        "topic": voluptuous.And(
            basestring, vu.NoSpaceCharacter())
    }, required=True)
    return config_schema(config)
