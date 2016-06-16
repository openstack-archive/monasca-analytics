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

import abc
import json
import logging
# TODO(David): Recursive import => File needs to be renamed
import random
import SocketServer
import threading as th
import time
import uuid

import numpy as np
import schema
import six

import monasca_analytics.exception.monanas as err
from monasca_analytics.source import base

logger = logging.getLogger(__name__)


class RandomSource(base.BaseSource):
    """A randomly generated data source implementation."""

    def __init__(self, _id, _config):
        super(RandomSource, self).__init__(_id, _config)
        try:
            self._configure_server()
        except IOError:
            raise err.MonanasInitError("Address already in use.")
        except AttributeError:
            raise err.MonanasInitError("Invalid generate or validate method.")

    def _configure_server(self):
        """Creates and configures the Server object

        The server object is configured according to
        the configuration of this source module
        """
        self._server = SocketServer.ThreadingTCPServer(
            (self._config["params"]["host"],
             self._config["params"]["port"]),
            MonanasTCPHandler, False)
        self._server.generate = getattr(
            self, "_generate_" +
            self._config["params"]["model"]["name"])
        # self._server.validate = getattr(
        #    source_model, self._config["validate"])
        self._server.allow_reuse_address = True
        self._server.server_bind()
        self._server.server_activate()
        self._server.terminate = False
        self._server.generate_alerts_per_second =\
            self._config["params"]["alerts_per_burst"]
        self._server.generate_idle_time_between_bursts =\
            self._config["params"]["idle_time_between_bursts"]
        self._server_thread = th.Thread(target=self._server.serve_forever)
        self._is_server_running = False

    @staticmethod
    def validate_config(_config):
        source_schema = schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
            "params": {
                "host": schema.And(basestring,
                                   lambda i: not any(c.isspace() for c in i)),
                "port": int,
                "model": {
                    "name": schema.And(basestring,
                                       lambda i: not any(c.isspace()
                                                         for c in i)),
                    "params": {
                        "origin_types": schema.And([
                            {
                                "origin_type": schema.And(
                                    basestring,
                                    lambda i: not any(c.isspace() for c in i)),
                                "weight": schema.And(schema.Or(int, float),
                                                     lambda w: w > 0.0)
                            }
                        ], lambda o: len(o) > 0),
                        schema.Optional("key_causes"): dict
                    }
                },
                "alerts_per_burst": schema.And(int, lambda a: a > 0),
                "idle_time_between_bursts": schema.And(schema.Or(int, float),
                                                       lambda i: i > 0)
            }
        })
        return source_schema.validate(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": RandomSource.__name__,
            "params": {
                "host": "localhost",
                "port": 1010,
                "model": {
                    "name": "my_model_name",
                    "params": {
                        "origin_types": [
                            {
                                "origin_type": "my_origin_type",
                                "weight": 1.0
                            }
                        ],
                    }
                },
                "alerts_per_burst": 1,
                "idle_time_between_bursts": 1.0
            }
        }

    def _start_server(self):
        if not self._is_server_running:
            self._server_thread.start()
            self._is_server_running = True

    def create_dstream(self, ssc):
        """Dstream object creation

        The _dstream object is created before this source is bound
        to the consumers. It uses a socketTextStream, to read data from
        the ThreadingTCPServer.

        :type ssc: pyspark.streaming.StreamingContext
        :param ssc: Spark Streaming Context
        """
        self._start_server()
        self._dstream = ssc.socketTextStream(
            self._config["params"]["host"],
            self._config["params"]["port"])

    def get_feature_list(self):
        raise NotImplementedError("This method needs to be implemented")

    def terminate_source(self):
        """Terminates the source with a delay

        Terminates the source with a delay to allow the messages
        being sent by the handler to clear up.
        """
        self._server.terminate = True
        time.sleep(1)
        self._server.server_close()
        self._server_thread = None

    def _generate_simple_model(self):
        """Generates an alert based on simple_model."""
        current_time = int(round(time.time() * 1000))
        return {
            "created": current_time,
            "id": str(uuid.uuid4()),
            "origin": str(uuid.uuid4()),
            "origin_type": self._random_origin_type(),
            "data": {},
            "state": "",
            "updated": current_time
        }

    def _random_origin_type(self):
        """Randomizes the origin_type"""
        origin_types = self._config[
            "params"]["model"]["params"]["origin_types"]
        return origin_types[self._weighted_choice(
            [o["weight"] for o in origin_types])]["origin_type"]

    def _weighted_choice(self, weights):
        """Gets an index chosen randomly but weighted from a list of weights"""
        totals = []
        running_total = 0

        for w in weights:
            running_total += w
            totals.append(running_total)

        rnd = random.random() * running_total

        for i, total in enumerate(totals):
            if rnd < total:
                return i


@six.add_metaclass(abc.ABCMeta)
class BaseDataSourceGenerator(object):
    """An interface for random data source generators."""

    @abc.abstractmethod
    def __init__(self, _config):
        """BaseDataSourceGenerator constructor.

        :type _config: dict
        :param _config: Configuration of this source
        """
        self._config = _config
        self.generate = getattr(self, "generate_" +
                                self._config["params"]["model"]["name"])

    @abc.abstractmethod
    def is_burst_over(self):
        """Should return true when all the burst alerts have been generated"""
        pass

    def generate_simple_model(self):
        """Generate alert event that are shaped according to the simple model
        """
        current_time = time.time()
        return {
            "created": current_time,
            "id": str(uuid.uuid4()),
            "origin": str(uuid.uuid4()),
            "origin_type": self._pick_next_type(),
            "data": {},
            "state": "",
            "updated": current_time
        }

    @abc.abstractmethod
    def _pick_next_type(self):
        """Should return the next type for the simple model generation"""
        pass


class LinearlyDependentDataSourceGenerator(BaseDataSourceGenerator):
    """A data source generator where alerts are linearly dependent

    :raises: exception -- if the causal matrix is cyclic
    """

    def __init__(self, config):
        BaseDataSourceGenerator.__init__(self, config)

        # Acyclic causality model
        config_key_causes = self._config[
            "params"]["model"]["params"]["key_causes"]

        # Create the causal matrix (/graph)
        self._features_names = config_key_causes.keys()
        n = len(self._features_names)
        self._causal_matrix = np.zeros((n, n), dtype=np.float32)
        for i in range(n):
            for j in range(n):
                row = self._features_names[i]
                col = self._features_names[j]
                if col in config_key_causes[row]:
                    self._causal_matrix[i, j] = 1

        # Triangulate the causal matrix
        tmp_matrix = np.copy(self._causal_matrix)
        n_t = tmp_matrix.shape[0]
        while n_t != 1:
            for i in range(n_t):
                if np.all(tmp_matrix[i, :] == np.zeros(n_t)):
                    tmp_matrix[[i, 0], :] = tmp_matrix[[0, i], :]
                    tmp_matrix[:, [i, 0]] = tmp_matrix[:, [0, i]]
                    k = n - n_t
                    r = i + k
                    self._causal_matrix[
                        [r, k], :] = self._causal_matrix[[k, r], :]
                    self._causal_matrix[
                        :, [r, k]] = self._causal_matrix[:, [k, r]]
                    self._features_names[r], self._features_names[
                        k] = self._features_names[k], self._features_names[r]
                    tmp_matrix = tmp_matrix[1:, 1:]
                    break
                if i == n_t - 1:
                    raise err.MonanasCyclicRandomSourceError
            n_t = tmp_matrix.shape[0]

        # Prepare a zero buffer that store the random values generated
        # following the causal model
        self._features_random_value = np.zeros(len(self._features_names))

        # This stack will contains the generated values for one burst (if that
        # make some sense)
        self._features_stack_emitted = []
        logger.debug(
            "Causality Matrix (RandomSource): {0}".format(
                self._causal_matrix))

    def is_burst_over(self):
        return len(self._features_stack_emitted) == 0

    def _pick_next_type(self):
        while len(self._features_stack_emitted) == 0:
            # Generate more features that follows the dag defined by the causal
            # matrix
            n = len(self._features_names)
            self._features_random_value = np.random.laplace(size=n)
            for i in range(n):
                self._features_random_value[
                    i] += np.dot(self._causal_matrix,
                                 self._features_random_value)[i]

            self._features_random_value = np.floor(self._features_random_value)
            for i in range(n):
                nb = np.abs(int(self._features_random_value[i]))
                if nb > 0:
                    feature = self._features_names[i]
                    self._features_stack_emitted.extend(
                        [feature for _ in range(nb)])
        return self._features_stack_emitted.pop()


class UncorrelatedDataSourceGenerator(BaseDataSourceGenerator):
    """A data source generator where alert item are not correlated.

    Each item has a unique probability to be generated.
    """

    def __init__(self, config):
        BaseDataSourceGenerator.__init__(self, config)
        self.accumulated_alerts = 0
        self._config = config

    def is_burst_over(self):
        is_over = self.accumulated_alerts == self._config[
            "params"]["alerts_per_burst"]
        if is_over:
            self.accumulated_alerts = 0
        return is_over

    def _pick_next_type(self):
        self.accumulated_alerts += 1
        origin_types = self._config[
            "params"]["model"]["params"]["origin_types"]
        origin_type = UncorrelatedDataSourceGenerator._weighted_choice(
            [o["weight"] for o in origin_types])
        return origin_types[origin_type]["origin_type"]

    @staticmethod
    def _weighted_choice(weights):
        """Gets an index chosen randomly but weighted from a list of weights"""
        totals = []
        running_total = 0

        for w in weights:
            running_total += w
            totals.append(running_total)

        rnd = random.random() * running_total

        for i, total in enumerate(totals):
            if rnd < total:
                return i


class MonanasTCPHandler(SocketServer.BaseRequestHandler):
    """A TCP server handler for the alert generation."""

    def handle(self):
        """Handles the incoming messages."""
        accumulated_alerts = 0

        while True and not self.server.terminate:
            alert = self.server.generate()

            try:
                validated_alert = self.server.validate(alert)
                self.request.send(json.dumps(validated_alert) + "\n")
                accumulated_alerts += 1
            except schema.SchemaError:
                logger.warn("Invalid schema for generated alerts.")

            time.sleep(self.server.generate_idle_time_between_bursts)
