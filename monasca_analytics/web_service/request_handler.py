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

import six
from tornado import web
import voluptuous

import monasca_analytics.banana.emitter as emit
import monasca_analytics.exception.monanas as err
import monasca_analytics.util.common_util as introspect
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

    def initialize(self, monanas, typeck_only):
        """Initialize the handler.

        :param monanas: A Monana's instance.
        """
        self._monanas = monanas
        self._typeck_only = typeck_only

    @web.asynchronous
    def post(self):
        """Performs a Monanas's action."""
        terminate = (False, "")

        try:
            body = json.loads(self.request.body)
            web_service_model.banana_model(body)
            emitter = emit.JsonEmitter()
            if self._typeck_only:
                self._monanas.typeck_configuration(body["content"],
                                                   emitter)
            else:
                self._monanas.try_change_configuration(body["content"],
                                                       emitter)
            self.write(emitter.result)
        except (AttributeError, voluptuous.Invalid, ValueError) as e:
            self.set_status(400, "The request body was malformed.")
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


class BananaMetaDataHandler(web.RequestHandler):

    def initialize(self, monanas):
        """Initializes the handler.

        :param monanas: Monanas -- A Monanas's instance.
        """
        self._monanas = monanas

    @web.asynchronous
    def get(self):
        all_components = introspect.get_available_classes()
        result = {"components": []}
        for kind, components in six.iteritems(all_components):
            for component in components:
                result["components"].append({
                    "name": component.__name__,
                    "description": component.__doc__,
                    "params": map(lambda x: x.to_json(),
                                  component.get_params()),
                })
        self.write(result)
        self.flush()
        self.finish()

    @web.asynchronous
    def post(self):

        try:
            body = json.loads(self.request.body)
            web_service_model.banana_model(body)
            type_table = self._monanas.compute_type_table(body["content"])
            self.write(type_table)
        except (AttributeError, voluptuous.Invalid, ValueError) as e:
            logger.warn("Wrong request: {}.".
                        format(e))
            self.set_status(400, "The request body was malformed.")
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            logger.error("Unexpected error: {}. {}".
                         format(sys.exc_info()[0], e))
            self.set_status(500, "Internal server error.")

        self.flush()
        self.finish()
