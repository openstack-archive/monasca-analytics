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
from monasca_analytics.source.markov_chain import events as ev
import monasca_analytics.source.markov_chain.prob_checks as pck
import monasca_analytics.source.markov_chain.state_check as dck
import monasca_analytics.source.markov_chain.transition as tr

logger = logging.getLogger(__name__)


class CloudMarkovChainSource(base.MarkovChainSource):

    @staticmethod
    def validate_config(_config):
        source_schema = schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
            "params": {
                "server_sleep_in_seconds": schema.And(float,
                                                      lambda v: 0 < v < 1)
            },
            "transitions": {
                "web_service": {
                    "run=>slow": {
                        schema.Use(int): schema.And(schema.Or(int, float),
                                                    lambda v: 0 <= v <= 1),
                    },
                    "slow=>run": {
                        schema.Use(int): schema.And(schema.Or(int, float),
                                                    lambda v: 0 <= v <= 1),
                    },
                    "stop=>run": schema.And(schema.Or(int, float),
                                            lambda v: 0 <= v <= 1),
                },
                "switch": {
                    "on=>off": schema.And(schema.Or(int, float),
                                          lambda v: 0 <= v <= 1),
                    "off=>on": schema.And(schema.Or(int, float),
                                          lambda v: 0 <= v <= 1),
                },
                "host": {
                    "on=>off": schema.And(schema.Or(int, float),
                                          lambda v: 0 <= v <= 1),
                    "off=>on": schema.And(schema.Or(int, float),
                                          lambda v: 0 <= v <= 1),
                },
            },
            "triggers": {
                "support": {
                    "get_called": {
                        schema.Use(int): schema.And(schema.Or(int, float),
                                                    lambda v: 0 <= v <= 1),
                    },
                },
            },
            "graph": {
                schema.And(basestring,
                           lambda s: len(s.split(":")) == 2 and
                           s.split(":")[1] in
                           ["host", "web_service", "switch"],
                           error="Key should be of the form 'anything:host' "
                                 "where 'host' can be replaced "
                                 "by 'web_service' or 'switch'."): [basestring]
            }
        })
        return source_schema.validate(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": CloudMarkovChainSource.__name__,
            "params": {
                "server_sleep_in_seconds": 0.01
            },
            "transitions": {
                "web_service": {
                    "run=>slow": {
                        "0": 0.001,
                        "8": 0.02,
                        "12": 0.07,
                        "14": 0.07,
                        "22": 0.03,
                        "24": 0.001
                    },
                    "slow=>run": {
                        "0": 0.99,
                        "8": 0.7,
                        "12": 0.1,
                        "14": 0.1,
                        "22": 0.8,
                        "24": 0.99
                    },
                    "stop=>run": 0.7
                },
                "host": {
                    "on=>off": 0.005,
                    "off=>on": 0.5
                },
                "switch": {
                    "on=>off": 0.01,
                    "off=>on": 0.7
                }
            },
            "triggers": {
                "support": {
                    "get_called": {
                        "0": 0.1,
                        "8": 0.2,
                        "12": 0.8,
                        "14": 0.8,
                        "22": 0.5,
                        "24": 0.0
                    }
                }
            },
            "graph": {
                "h1:host": ["s1"],
                "h2:host": ["s1"],
                "s1:switch": [],
                "w1:web_service": ["h1"],
                "w2:web_service": ["h2"]
            }
        }

    def get_feature_list(self):
        node_names = [k.split(":")[0]
                      for k in dict(self._config["graph"]).keys()]
        node_names.append("support_1")
        return node_names

    def _create_system(self):
        triggers = self._create_event_triggers()
        markov_chains = self._create_markov_chain_models()
        graph = self._config["graph"]
        nodes = {}
        support_node = base.StateNode(None,
                                      markov_chains["support"],
                                      triggers["support"],
                                      _id="support_1")

        for k in graph.keys():
            node_name, node_type = k.split(":")
            if node_type == "host":
                nodes[node_name] = base.StateNode("on", markov_chains["host"],
                                                  triggers["host"],
                                                  _id=node_name)
            elif node_type == "switch":
                nodes[node_name] = base.StateNode("on",
                                                  markov_chains["switch"],
                                                  triggers["switch"],
                                                  _id=node_name)
            elif node_type == "web_service":
                webs = base.StateNode("run", markov_chains["web_service"],
                                      triggers["web_service"],
                                      _id=node_name)
                support_node.dependencies.append(webs)
                nodes[node_name] = webs

        for k, v in graph.iteritems():
            node_name, _ = k.split(":")

            for depend_on in v:
                if depend_on not in nodes:
                    logger.warn(
                        "Configuration error: '{}'"
                        " is not a proper dependency"
                        " of '{}'".format(depend_on, node_name))
                else:
                    n = nodes[node_name]
                    o = nodes[depend_on]
                    n.dependencies.append(o)

        return [support_node]

    def _create_event_triggers(self):
        triggers = self._config["triggers"]
        sup_tr = triggers["support"]
        user_support = ev.Trigger(
            prob_check=pck.ProbCheck(sup_tr["get_called"]),
            node_check=dck.AnyDepCheck(dck.NeqCheck("run")),
            event_builder=ev.EventBuilder(
                "User complained for poor web service"))
        webs1 = ev.Trigger(
            node_check=dck.OrCheck(
                dck.EqCheck("stop"),
                dck.DepCheck(dck.EqCheck("off")),
                dck.DepCheck(dck.DepCheck(dck.EqCheck("off")))
            ),
            prob_check=pck.NoProbCheck(),
            event_builder=ev.EventBuilder("Application is down")
        )
        webs2 = ev.Trigger(
            node_check=dck.EqCheck("slow"),
            prob_check=pck.NoProbCheck(),
            event_builder=ev.EventBuilder("Application is slow")
        )
        host = ev.Trigger(
            node_check=dck.OrCheck(dck.EqCheck("off"),
                                   dck.DepCheck(dck.EqCheck("off"))),
            prob_check=pck.NoProbCheck(),
            event_builder=ev.EventBuilder("Host is unreachable or down")
        )
        switch = ev.Trigger(
            node_check=dck.EqCheck("off"),
            prob_check=pck.NoProbCheck(),
            event_builder=ev.EventBuilder("Switch is unreachable or down")
        )

        return {
            "switch": switch,
            "host": host,
            "web_service": [webs1, webs2],
            "support": user_support
        }

    def _create_markov_chain_models(self):
        transitions = self._config["transitions"]

        # Switch Transitions
        sw_tr = transitions["switch"]
        tr1 = tr.Transition(
            from_state="on", to_state="off",
            prob_check=pck.ProbCheck(sw_tr["on=>off"]))
        tr2 = tr.Transition(
            from_state="off", to_state="on",
            prob_check=pck.ProbCheck(sw_tr["off=>on"]))
        switch_mc = tr.MarkovChain([tr1, tr2])

        # Host Transitions
        hs_tr = transitions["host"]
        tr1 = tr.Transition(
            from_state="on", to_state="off",
            prob_check=pck.ProbCheck(hs_tr["on=>off"]))
        tr2 = tr.Transition(
            from_state="off", to_state="on",
            prob_check=pck.ProbCheck(hs_tr["off=>on"]))
        host_mc = tr.MarkovChain([tr1, tr2])

        # Web service Transitions
        ws_tr = transitions["web_service"]
        tr1 = tr.Transition(
            from_state="run", to_state="stop",
            prob_check=pck.NoProbCheck(),
            deps_check=dck.EqCheck("off"))
        tr2 = tr.Transition(
            from_state="slow", to_state="stop",
            prob_check=pck.NoProbCheck(),
            deps_check=dck.EqCheck("off"))
        tr3 = tr.Transition(
            from_state="slow", to_state="run",
            prob_check=pck.NoProbCheck(),
            deps_check=dck.AndCheck(
                dck.EqCheck("on"),
                dck.DepCheck(dck.EqCheck("off"))))
        tr4 = tr.Transition(
            from_state="run", to_state="slow",
            prob_check=pck.ProbCheck(ws_tr["run=>slow"]),
            deps_check=dck.AndCheck(
                dck.EqCheck("on"),
                dck.DepCheck(dck.EqCheck("on"))))
        tr5 = tr.Transition(
            from_state="slow", to_state="run",
            prob_check=pck.ProbCheck(ws_tr["slow=>run"]),
            deps_check=dck.AndCheck(
                dck.EqCheck("on"),
                dck.DepCheck(dck.EqCheck("on"))))
        tr6 = tr.Transition(
            from_state="stop", to_state="run",
            prob_check=pck.ProbCheck(ws_tr["stop=>run"]),
            deps_check=dck.EqCheck("on"))
        webs_mc = tr.MarkovChain([tr1, tr2, tr3, tr4, tr5, tr6])

        # User support markov chain
        sup_mc = tr.MarkovChain([])

        return {
            "switch": switch_mc,
            "host": host_mc,
            "web_service": webs_mc,
            "support": sup_mc
        }
