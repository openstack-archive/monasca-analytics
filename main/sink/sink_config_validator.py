#!/usr/bin/env python

"""A list of functions for validating sink configs."""

import schema

from main.config import const
from main.util import common_util as cu


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
