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

import json
import logging
import sys
import traceback

from tornado import web
import voluptuous

import monasca_analytics.banana.emitter as emit
import monasca_analytics.exception.monanas as err
from monasca_analytics.web_service import web_service_model


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
            web_service_model.action_model(body)
            getattr(self._monanas, body["action"])()
        except (AttributeError, voluptuous.Invalid, ValueError):
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


class BananaHandler(web.RequestHandler):
    """
    Request handler to manage the active config using
    the banana configuration language.
    """

    def initialize(self, monanas):
        """Initialize the handler.

        :param monanas: A Monana's instance.
        """
        self._monanas = monanas

    @web.asynchronous
    def post(self):
        """Performs a Monanas's action."""
        terminate = (False, "")

        try:
            body = json.loads(self.request.body)
            web_service_model.banana_model(body)
            emitter = emit.JsonEmitter()
            # TODO(Joan): Change that
            self._monanas.try_change_configuration(body["content"], emitter)
            self.write(emitter.result)
        except (AttributeError, voluptuous.Invalid, ValueError):
            self.set_status(400, "The request body was malformed.")
        except (err.MonanasBindSourcesError,
                err.MonanasAlreadyStartedStreaming,
                err.MonanasAlreadyStoppedStreaming) as e:
            self.set_status(400, e.__str__())
        except err.MonanasStreamingError as e:
            self.set_status(500, e.__str__())
            terminate = (True, e.__str__())
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            logger.error("Unexpected error: {0}. {1}".
                         format(sys.exc_info()[0], e))
            self.set_status(500, "Internal server error.")

        self.flush()
        self.finish()

        if terminate[0]:
            logger.error(terminate[1])
            self._monanas.stop_streaming_and_terminate()
