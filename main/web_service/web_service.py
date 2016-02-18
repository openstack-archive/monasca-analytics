#!/usr/bin/env python

from tornado import web

from main.web_service import request_handler


class WebService(web.Application):
    """WebService serving REST API for Monanas."""

    def __init__(self, monanas, config):
        """WebService constructor."""
        self._monanas = monanas
        self._config = config
        handlers = [
            (r"/", request_handler.MonanasHandler, {"monanas": self._monanas})
        ]

        settings = {}

        web.Application.__init__(self,
                                 handlers,
                                 debug=config["debug"],
                                 **settings)
