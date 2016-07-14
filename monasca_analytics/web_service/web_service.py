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

from tornado import web

from monasca_analytics.web_service import request_handler


class WebService(web.Application):
    """WebService serving REST API for Monanas."""

    def __init__(self, monanas, config):
        """WebService constructor."""
        self._monanas = monanas
        self._config = config
        params = {"monanas": self._monanas}
        handlers = [
            (r"/", request_handler.MonanasHandler, params),
            (r"/banana", request_handler.BananaHandler, params),
        ]

        settings = {}

        web.Application.__init__(self,
                                 handlers,
                                 debug=config["debug"],
                                 **settings)
