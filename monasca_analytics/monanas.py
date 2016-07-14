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

import logging
import os
import sys

from tornado import ioloop
import voluptuous

import monasca_analytics.banana.emitter as emit
import monasca_analytics.banana.pass_manager as executor
import monasca_analytics.exception.monanas as err
import monasca_analytics.spark.driver as driver
import monasca_analytics.util.common_util as cu
import monasca_analytics.web_service.web_service as ws

logger = logging.getLogger(__name__)

debugging = False


class Monanas(object):
    """Monanas.

    Monanas entry point. This class implements the high level functions to
    manage the streaming.

    Currently: start and stop.
    """

    def __init__(self, _config):
        """Monanas constructor.

        It validates the configuration passed as parameter and,
        if it is fine, it creates the components defined by it.

        :type _config: dict
        :param _config: configuration of the system.
        """
        self._is_streaming = False
        self._driver = driver.DriverExecutor(_config)
        logger.info("Monanas initialized.")

    def is_streaming(self):
        """Gets the status of streaming.

        :rtype: bool
        :returns: `True` if Monanas is streaming,`False` otherwise.
        """
        return self._is_streaming

    def try_change_configuration(self, banana_str, emitter):
        """Try to change the configuration to the provided one.

        :type banana_str: str
        :param banana_str: New configuration.
        :type emitter: emit.JsonEmitter
        :param emitter: a Json emitter instance
        """
        if not isinstance(emitter, emit.JsonEmitter):
            raise err.MonanasException()
        # Try to change the configuration.
        executor.execute_banana_string(banana_str, self._driver, emitter)

    def start_streaming(self):
        """Starts streaming data.

        :raises: MonanasStreamingError -- if one or more sources fail to bind
        or StreamingContext fails to start.
        :raises: MonanasAlreadyStartedStreaming -- if Monanas is already
        streaming.
        """
        if not self._is_streaming:
            try:
                self._driver.start_pipeline()
                self._is_streaming = True
            except Exception:
                raise err.MonanasStreamingError()
        else:
            raise err.MonanasAlreadyStartedStreaming()

    def stop_streaming(self):
        """Stops streaming data.

        :raises: MonanasAlreadyStoppedStreaming -- if Monanas is not streaming
        """
        if self._is_streaming:
            self._driver.stop_pipeline()
            self._is_streaming = False
        else:
            raise err.MonanasAlreadyStoppedStreaming()

    def stop_streaming_and_terminate(self):
        """Stops streaming data and terminate Monanas."""
        try:
            self.stop_streaming()
            logger.info("All streaming stopped.")
        except (err.MonanasAlreadyStoppedStreaming, NameError):
            logger.info("All streaming stopped.")
        logger.info("Monanas stopped.")
        os.kill(os.getpid(), 1)


if __name__ == "__main__":
    monanas = None
    if debugging:
        import pydevd
        pydevd.settrace(suspend=False)
    try:
        try:
            cu.setup_logging(sys.argv[2])
        except IOError:
            raise err.MonanasMainError("File not found: \
                `{0}`.".format(sys.argv[2]))
        except ValueError:
            raise err.MonanasMainError("`{0}` is not a valid logging \
                config file.".format(sys.argv[2]))

        logger = logging.getLogger(__name__)

        try:
            config = cu.parse_json_file(sys.argv[1])
        except IOError:
            raise err.MonanasMainError("File not found: \
                `{0}`.".format(sys.argv[1]))
        except ValueError as e:
            raise err.MonanasMainError("`{0}` is not a \
                valid json file.".format(sys.argv[1]))
        except voluptuous.Invalid:
            raise err.MonanasMainError("`{0}` has an \
                invalid schema.".format(sys.argv[1]))

        monanas = Monanas(config)
        web_service = ws.WebService(monanas, config["server"])
        web_service.listen(config["server"]["port"])
        ioloop.IOLoop.instance().start()
    except IOError as e:
        logger.error("Address already in use.")
    except (err.MonanasInitError, err.MonanasMainError) as e:
        logger.error(e.__str__())
    except KeyboardInterrupt:
        try:
            if monanas is not None:
                monanas.stop_streaming_and_terminate()
        except NameError:
            logger.info("Premature termination.")
    except Exception as e:
        logger.error("Unexpected error: {0}. {1}.".
                     format(sys.exc_info()[0], e))

        try:
            if monanas is not None:
                monanas.stop_streaming_and_terminate()
        except NameError:
            logger.info("Premature termination.")

        logger.info("Monanas stopped.")
