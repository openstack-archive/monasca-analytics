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

import schema

from monasca_analytics.sink import base


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
