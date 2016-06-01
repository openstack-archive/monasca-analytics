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

        :type node_check:
            (monasca_analytics.source.markov_chain.base.StateNode) -> bool
        :param node_check:
            Checker function that will return true if the node has an
                           appropriate type
        :type prob_check: (int) -> bool
        :param prob_check:
            A bernoulli trial that randomly return true or false that
            can use the parameter (hour of the day) to modify the
            probability of success

        :type event_builder:
            (monasca_analytics.source.markov_chain.base.StateNode) -> Event
        :param event_builder:  Event builder that receive the node and use
                               the state to return an event.
        """
        self._prob_check = prob_check
        self._node_check = node_check
        self._event_builder = event_builder

    def apply_on(self, node, hour_of_day):
        """Apply this trigger on the given node.

        :type node: monasca_analytics.source.markov_chain.base.StateNode
        :param  node: Node to test the trigger with.
        :type hour_of_day: int
        :param hour_of_day: An integer between [0, 24) representing
                            the hour of the day.
        """
        if self._prob_check(hour_of_day) and self._node_check(node):
            return self._event_builder(node)
        return None


class Event(object):

    def __init__(self, msg, ident):
        """
        :type msg: str
        :param msg: The event message.
        :type ident: str
        :param ident: The id of the node causing this event.
        """
        self.id = ident
        self.msg = msg


class EventBuilder(object):

    def __init__(self, msg):
        """
        :type msg: str
        :param msg: The event message.
        """
        self._msg = msg

    def __call__(self, node):
        """
        :type node: monasca_analytics.source.markov_chain.base.StateNode
        :param node: The node associated with the event.
        """
        return Event(self._msg, str(node.id()))
