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

import schema

from monasca_analytics.config import const
from monasca_analytics.util import common_util as cu


def validate_kafka_sink_config(config):
    """Validates the KafkaSink configuration"""

    available_sink_classes = \
        cu.get_available_classes(const.SINKS)[const.SINKS]
    available_sink_names = [Clazz.__name__ for Clazz in available_sink_classes]

    config_schema = schema.Schema({
        "module": schema.And(basestring,
                             lambda m: m in available_sink_names),
        "params": {
            "host": schema.And(basestring,
                               lambda i: not any(c.isspace() for c in i)),
            "port": int,
            "topic": schema.And(basestring,
                                lambda i: not any(c.isspace() for c in i))
        }
    })

    return config_schema.validate(config)
