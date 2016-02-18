#!/usr/bin/env python

import schema

from main.sink import base


class StdoutSink(base.BaseSink):
    """Sink that prints the dstream to stdout, using pprint command"""

    def sink_dstream(self, dstream):
        dstream.pprint()

    def sink_ml(self, voter_id, matrix):
        pass

    @staticmethod
    def get_default_config():
        return {"module": StdoutSink.__name__}

    @staticmethod
    def validate_config(_config):
        return schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i))
        }).validate(_config)
