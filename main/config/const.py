#!/usr/bin/env python

import copy

SOURCES = "sources"
INGESTORS = "ingestors"
SMLS = "smls"
VOTERS = "voters"
SINKS = "sinks"
LDPS = "ldps"
CONNECTIONS = "connections"
# FEEDBACK = "feedback"

components_types = [SOURCES, INGESTORS, SMLS, VOTERS, SINKS, LDPS]


_default_base_config = {
    "spark_config": {
        "appName": "testApp",
        "streaming": {
            "batch_interval": 1
        }
    },
    "server": {
        "port": 3000,
        "debug": False
    },
    "sources": {},
    "ingestors": {},
    "smls": {},
    "voters": {},
    "sinks": {},
    "ldps": {},
    "connections": {},
    "feedback": {}
}


def get_default_base_config():
    return copy.deepcopy(_default_base_config)
