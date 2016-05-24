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


class Trigger(object):
    """A trigger generate events when a particular graph state is reached."""

    def __init__(self, node_check, prob_check, event_builder):
        """Create a new trigger.

        :param node_check: function (main.source.markov_chain.base.StateNode)
        -> bool -- Checker function that will return true if the node has an
        appropriate type
        :param prob_check: function (int) -> bool -- A probability check that
        can return true or false with a random chance
        :param event_builder: function (main.source.markov_chain.base.
        StateNode)-> Event -- Event builder that receive the node and use
        the state to return an event.
        """
        self._prob_check = prob_check
        self._node_check = node_check
        self._event_builder = event_builder

    def apply_on(self, node, hour_of_day):
        """
        :param node: main.source.markov_chain.base.StateNode
        :param hour_of_day: int
        """
        if self._prob_check(hour_of_day) and self._node_check(node):
            return self._event_builder(node)
        return None


class Event(object):

    def __init__(self, msg, ident):
        """
        :param msg: str
        :param ident: str
        """
        self.id = ident
        self.msg = msg


class EventBuilder(object):

    def __init__(self, msg):
        """
        :param msg: str
        """
        self._msg = msg

    def __call__(self, node):
        """
        :param node: main.source.markov_chain.base.StateNode
        """
        return Event(self._msg, str(node.id()))
