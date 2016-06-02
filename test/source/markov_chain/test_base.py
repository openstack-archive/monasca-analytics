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
import os
import unittest

from monasca_analytics.source.markov_chain import base
import monasca_analytics.source.markov_chain.events as ev
import monasca_analytics.source.markov_chain.prob_checks as pck
import monasca_analytics.source.markov_chain.state_check as dck
import monasca_analytics.source.markov_chain.transition as tr


class StateNodeTest(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        self.setup_logging()

    def tearDown(self):
        pass

    def test_collect_events_should_be_populated_by_trigger(self):
        some_trigger = ev.Trigger(
            node_check=dck.EqCheck(0),
            prob_check=pck.NoProbCheck(),
            event_builder=ev.EventBuilder("test")
        )
        node = base.StateNode(0, None, some_trigger)
        events = node.collect_events(1)
        self.assertTrue(len(events) == 1)
        self.assertEqual(events[0].msg, "test", "a")

    def test_next_state_should_use_available_transitions(self):
        tr1 = tr.Transition(
            from_state=0,
            to_state=1,
            deps_check=dck.TrueCheck(),
            prob_check=pck.NoProbCheck()
        )
        tr2 = tr.Transition(
            from_state=1,
            to_state=2,
            deps_check=dck.EqCheck(1),
            prob_check=pck.NoProbCheck()
        )
        mc = tr.MarkovChain([tr1, tr2])
        n1 = base.StateNode(0, mc, None)
        n2 = base.StateNode(1, mc, None)
        n3 = base.StateNode(0, mc, None)
        n1.dependencies.append(n2)
        n2.dependencies.append(n3)
        # First round
        n1.next_state(1, set())
        self.assertEqual(n1.state, 1)
        self.assertEqual(n2.state, 1)
        self.assertEqual(n3.state, 0)
        # Second round
        n1.next_state(1, set())
        self.assertEqual(n1.state, 2)
        self.assertEqual(n2.state, 1)
        self.assertEqual(n3.state, 0)

    def test_next_state_update_only_deps_and_deps_in_first(self):
        tr1 = tr.Transition(
            from_state=0,
            to_state=1,
            prob_check=pck.NoProbCheck()
        )
        tr2 = tr.Transition(
            from_state=1,
            to_state=2,
            deps_check=dck.EqCheck(1),
            prob_check=pck.NoProbCheck()
        )
        mc = tr.MarkovChain([tr1, tr2])
        n1 = base.StateNode(0, mc, None)
        n2 = base.StateNode(1, mc, None)
        n3 = base.StateNode(0, mc, None)
        n1.dependencies.append(n2)
        n2.dependencies.append(n3)
        n2.next_state(1, set())
        self.assertEqual(n1.state, 0)
        self.assertEqual(n2.state, 2)
        self.assertEqual(n3.state, 1)


if __name__ == "__main__":
    unittest.main()
