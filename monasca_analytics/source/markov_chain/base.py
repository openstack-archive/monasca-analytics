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
import datetime
import itertools
import json
import logging
import six
import SocketServer
import threading
import time

from monasca_analytics.source import base

logger = logging.getLogger(__name__)


class MarkovChainSource(base.BaseSource):
    """Base Source of data generated according a Markov chain model.

    A Markov chain model baked by a finite state machine
    to model more realistic scenario with optional confounding variables.
    This source is useful to see how causality is discovered in the presence
    of confounding variable as well as scenario where some alert appears only
    in a deterministic fashion.
    """

    @abc.abstractmethod
    def _create_system(self):
        """
        Abstract method that should be implemented by subclasses

        :rtype: list[StateNode]
        :returns: List of StateNode that do not have any dependencies
        """
        pass

    def create_dstream(self, ssc):
        """Initiates the system in a TCP server, and creates the dstream object

        The _dstream object is created before this source is bound
        to the consumers. It uses a socketTextStream, to read data from
        the ThreadingTCPServer.

        :type ssc: pyspark.streaming.StreamingContext
        :param ssc: Spark Streaming Context that provides the data input
        """
        system = LeafNodes(self._create_system())
        port = self._start_thread(system)
        return ssc.socketTextStream(
            "localhost",
            port)

    def terminate_source(self):
        # This is to allow all the messages
        # being sent by the handler to clear up.
        self._server.terminate = True
        self._server.shutdown()
        self._server.server_close()
        self._server_thread.join(0.1)

    def _start_thread(self, system):
        self._server = SocketServer.ThreadingTCPServer(
            ("", 0),        # Let the OS pick a port for us
            FMSTCPHandler,  # Handler of the requests
            False)
        self._server.allow_reuse_address = True
        self._server.server_bind()
        self._server.server_activate()
        self._server.terminate = False
        self._server.system = system
        self._server.sleep_in_seconds = self._config["sleep"]

        self._server_thread = threading.Thread(target=self._serve_forever)
        self._server_thread.start()
        port_used = self._server.socket.getsockname()[1]
        return port_used

    def _serve_forever(self):
        try:
            self._server.serve_forever()
        except IOError:
            logger.debug("Markov chain source's server stopped.")


class MetaId(abc.ABCMeta):

    def __new__(mcs, name, bases, namespace):  # @NoSelf
        cls = super(abc.ABCMeta, mcs).__new__(mcs, name, bases, namespace)
        cls.ids = itertools.count(1)
        return cls


class LeafNodes(object):

    def __init__(self, state_nodes):
        """Constructor with list of state nodes

        :type state_nodes: list[StateNode]
        :param state_nodes: The node of the directed acyclic graph
                            that has no dependencies.
        """
        self._state_nodes = state_nodes

    def next_state(self, hour_of_day):
        """Move to next state

        :type hour_of_day: int
        :param hour_of_day: An hour of the day that is used by
                            StateNode.next_state
        """
        ignored_states = set([])
        for s in self._state_nodes:
            s.next_state(hour_of_day, ignored_states)

    def collect_events(self, hour_of_day, fake_date, request):
        """Get list of events

        :type hour_of_day: int
        :param hour_of_day: An hour of the day that is used by
                            StateNode.collect_event
        :type fake_date: datetime.datetime
        :param fake_date: A date that you can use to generate a ctime.
        :type request: RequestBuilder
        :param request: Request object to send data.
        :rtype: list
        :returns: List of event. Specific to the event builder.
        """
        for node in self._state_nodes:
            node.collect_events(hour_of_day, fake_date, request)


@six.add_metaclass(MetaId)
class StateNode(object):
    """This class describes a particular node in the dependency graph.

    It holds the state information relative to that node and the
    dependencies with the other nodes. The Markov
    It is managed by one instance of a StateDescriptor.
    """

    def __init__(self, initial_state, markov_chain, trigger, _id=None):
        """Constructor

        :type _id: int | str
        :param _id: Id of the node
        :type initial_state: str | int | None
        :param initial_state: Initial state for this node.
        :type markov_chain:
            monasca_analytics.source.markov_chain.transition.MarkovChain
        :param markov_chain: Markov Chain managing this node state.
        :type trigger:
            list | monasca_analytics.source.markov_chain.events.Trigger
        :param trigger: List of triggers or single trigger that you want
                        to attached to this node.
        """
        if _id is None:
            self._id = next(self.__class__.ids)
        else:
            self._id = _id
        self.state = initial_state
        self._markov_chain = markov_chain
        if type(trigger) == list:
            self._triggers = trigger
        else:
            self._triggers = [trigger]
        self.dependencies = []

    def id(self):
        """
        :rtype: int | str
        :returns: Returns this object id.
        """
        return self._id

    def next_state(self, hour_of_day, ignored_states):
        """Move this element to the next state if it is not in the ignored set

        This will affect this element's children that conditionally depends
        on this element's state.

        :type hour_of_day: int
        :param hour_of_day: An integer in the range of 0 to 24 to
                            express the hour of the day.
        :type ignored_states: set
        :param ignored_states: set of states that should not change.
        """
        if self._id not in ignored_states:
            ignored_states.add(self._id)
            for dep in self.dependencies:
                dep.next_state(hour_of_day, ignored_states)
            self._markov_chain.apply_on(self, hour_of_day)

    def collect_events(self, hour_of_day, fake_date, request):
        """Collect event triggered for the next burst.

        :type hour_of_day: int
        :param hour_of_day: an integer in the range of 0 to 24 to express
                            he hour of the day.
        :type fake_date: datetime.datetime
        :param fake_date: A date that you can use to generate a ctime.
        :type request: RequestBuilder
        :param request: Request builder to send specific events
        :rtype: list
        :returns: events for this step or None
        """
        for trigger in self._triggers:
            trigger.apply_on(self, hour_of_day, fake_date, request)
        for dep in self.dependencies:
            dep.collect_events(hour_of_day, fake_date, request)


class FMSTCPHandler(SocketServer.BaseRequestHandler):
    """A TCP server handler for the alert generation."""

    def handle(self):
        """Handles incoming connection and pushing data into them."""

        fake_date = datetime.datetime.today()
        hour_of_day = fake_date.hour
        while not self.server.terminate:
            self.server.system.next_state(hour_of_day)
            request = RequestBuilder(self.request)
            self.server.system.collect_events(hour_of_day, fake_date, request)

            try:
                request.finalize()
            except IOError:
                logger.debug("Source is now off")
                self.server.terminate = True

            time.sleep(self.server.sleep_in_seconds)

            hour_of_day += 1
            fake_date += datetime.timedelta(hours=1)
            if hour_of_day > 24:
                hour_of_day = 0


class RequestBuilder(object):

    def __init__(self, request):
        self._request = request
        self._collected_data = []

    def send(self, data):
        """
        Send an object over the network.
        :param data: Object to send.
        """
        self._collected_data.append(data)

    def finalize(self):
        for data in self._collected_data:
            self._request.send("{0}\n".format(json.dumps(data,
                                                         cls=DictEncoder)))
        self._request = None
        self._collected_data = None


class DictEncoder(json.JSONEncoder):

    def default(self, o):
        return o.__dict__
