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

import logging

import schema

from monasca_analytics.source.markov_chain import base
from monasca_analytics.source.markov_chain import events
from monasca_analytics.source.markov_chain import prob_checks as pck
import monasca_analytics.source.markov_chain.state_check as dck
import monasca_analytics.source.markov_chain.transition as tr

logger = logging.getLogger(__name__)

STATE_STOP = "stop"
STATE_NORMAL = "normal"
STATE_ATTACK = "ping_flood_attack"

iptables = {"INPUT -i eth0 -p tcp --dport 22 -j ACCEPT": "ssh0",
            "OUTPUT -o eth0 -p tcp --sport 22 -j ACCEPT": "ssh1",
            "INPUT -s 1.2.3.4 -j DROP": "ip0",
            "INPUT -s 5.6.7.8 -j DROP": "ip1",
            "INPUT -s 1.2.1.2 -j DROP": "ip2",
            "INPUT -s 6.5.4.3 -j DROP": "ip3",
            "INPUT -i eth0 -p tcp --dport 80 -j ACCEPT": "http0",
            "OUTPUT -o eth0 -p tcp --sport 80 -j ACCEPT": "http1",
            "INPUT -p icmp --icmp-type echo-request -j ACCEPT": "ping0",
            "OUTPUT -p icmp --icmp-type echo-reply -j ACCEPT": "ping1",
            "OUTPUT -p icmp --icmp-type echo-request -j ACCEPT": "ping2",
            "INPUT -p icmp --icmp-type echo-reply -j ACCEPT": "ping3"}


iptable_types = ["ssh", "ip", "http", "ping"]


def get_iptable_type(identifier):
    for ip_type in iptable_types:
        if identifier.startswith(ip_type):
            return ip_type


class IPTablesSource(base.MarkovChainSource):
    """This source class implements an IPTable triggering emulator.

    It models a network system where iptables are triggered following
    a specific probability depending on the state of the Markov chain.
    """

    @staticmethod
    def validate_config(_config):
        source_schema = schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
            "params": {
                "server_sleep_in_seconds": schema.And(float,
                                                      lambda v: 0 < v < 1)
            }
        })
        return source_schema.validate(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": IPTablesSource.__name__,
            "params": {
                "server_sleep_in_seconds": 0.01
            }
        }

    def get_feature_list(self):
        return iptable_types

    def _create_system(self):
        """Markov Chain of IPTables being triggered in each state.

        Implements the Markov Chain model corresponding to the IPTables that
        are triggered depending on the state.
        In order to create the model, we have to create the triggers
        (events with some probability for each state),
        and the Markov chain model (probabilities of state transitions).
        """
        logger.debug("Creating IPTables System")
        triggers = self._create_event_triggers()
        logger.debug("Generated " + str(len(triggers)) +
                     " IPTables event triggers")
        markov_chain = self._create_markov_chain_model()
        logger.debug("Created Markov chain model for IPTables")
        support_node = base.StateNode(STATE_STOP,
                                      markov_chain,
                                      triggers)
        return [support_node]

    def _create_markov_chain_model(self):
        """Defines the Markov chain transitions.

        The transition will happen with the probability defined by ProbCheck,
        which will be evaluated each server_sleep_in_seconds time
        (defined by config). The values are quite low because the time when
        these are evaluated is the same as when the traffic is evaluated.
        Over time, the probability accumulation is much higher, though.
        """
        tr_stop_normal = tr.Transition(
            from_state=STATE_STOP, to_state=STATE_NORMAL,
            prob_check=pck.ProbCheck(0.8))
        tr_normal_stop = tr.Transition(
            from_state=STATE_NORMAL, to_state=STATE_STOP,
            prob_check=pck.ProbCheck(0.001))
        tr_normal_attack = tr.Transition(
            from_state=STATE_NORMAL, to_state=STATE_ATTACK,
            prob_check=pck.ProbCheck(0.0001))
        tr_attack_normal = tr.Transition(
            from_state=STATE_ATTACK, to_state=STATE_NORMAL,
            prob_check=pck.ProbCheck(0.2))
        return tr.MarkovChain([tr_stop_normal,
                               tr_normal_stop,
                               tr_normal_attack,
                               tr_attack_normal])

    def _create_event_triggers(self):
        """Defines the events that will be triggered in each state."""
        return self._create_normal_traffic_behaviour() +\
            self._create_ping_flood_traffic_behaviour()

    def _create_normal_traffic_behaviour(self):
        """These are the triggers that will happen in the NORMAL state.

        The http traffic is predominant, but there is also some ping traffic,
        and a little bit of ssh traffic
        """
        tr = []
        for iptable, feature in iptables.iteritems():
            if feature.startswith("ssh"):
                tr.append(self._create_trigger(0.1, STATE_NORMAL, iptable))
            elif feature.startswith("http"):
                tr.append(self._create_trigger(0.6, STATE_NORMAL, iptable))
            elif feature.startswith("ping"):
                tr.append(self._create_trigger(0.2, STATE_NORMAL, iptable))
        return tr

    def _create_ping_flood_traffic_behaviour(self):
        """These are the triggers that will happen in the ATTACK state.

        The ssh and http traffic is the same as in the normal state,
        but the ping traffic is dramatically increased
        """
        tr = []
        for iptable, feature in iptables.iteritems():
            if feature.startswith("ssh"):
                tr.append(self._create_trigger(0.1, STATE_ATTACK, iptable))
            elif feature.startswith("http"):
                tr.append(self._create_trigger(0.6, STATE_ATTACK, iptable))
            elif feature.startswith("ping"):
                tr.append(self._create_trigger(0.95, STATE_ATTACK, iptable))
        return tr

    def _create_trigger(self, prob, state, event_msg):
        """Aux function to create an event trigger

        :param prob: float between 0 and 1 -- probability of the event
        being triggered
        :param state: str -- State where this event can be triggered
        :param event_msg: str -- message that will be sent for this event
        """
        return events.Trigger(
            prob_check=pck.ProbCheck(prob),
            node_check=dck.EqCheck(state),
            event_builder=events.EventBuilder(event_msg))
