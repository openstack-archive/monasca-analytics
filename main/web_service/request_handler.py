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

import json
import logging
import sys

import schema
from tornado import web

import main.exception.monanas as err
from main.web_service import web_service_model


logger = logging.getLogger(__name__)


class MonanasHandler(web.RequestHandler):
    """Request handler for WebService."""

    def initialize(self, monanas):
        """Initializes the handler.

        :param monanas: Monanas -- A Monanas's instance.
        """
        self._monanas = monanas

    @web.asynchronous
    def post(self):
        """Performs a Monanas's action."""
        terminate = (False, "")

        try:
            body = json.loads(self.request.body)
            validated_body = getattr(web_service_model, "action_model")(body)
            getattr(self._monanas, validated_body["action"])()
        except (AttributeError, schema.SchemaError, ValueError):
            self.set_status(400, "The request body was malformed.")
        except (err.MonanasBindSourcesError,
                err.MonanasAlreadyStartedStreaming,
                err.MonanasAlreadyStoppedStreaming) as e:
            self.set_status(400, e.__str__())
        except err.MonanasStreamingError as e:
            self.set_status(500, e.__str__())
            terminate = (True, e.__str__())
        except Exception as e:
            logger.error("Unexpected error: {0}. {1}".
                         format(sys.exc_info()[0], e))
            self.set_status(500, "Internal server error.")

        self.flush()
        self.finish()

        if terminate[0]:
            logger.error(terminate[1])
            self._monanas.stop_streaming_and_terminate()
