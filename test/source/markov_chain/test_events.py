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

import main.source.markov_chain.events as ev
import main.source.markov_chain.prob_checks as pck
import main.source.markov_chain.state_check as dck


class DummyState(object):

    def __init__(self, state=0):
        self.state = state
        self.dependencies = []

    def id(self):
        return 0


class TriggersTest(unittest.TestCase):

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

    def test_trigger_should_create_event_when_necessary(self):
        some_trigger = ev.Trigger(
            node_check=dck.EqCheck(0),
            prob_check=pck.NoProbCheck(),
            event_builder=ev.EventBuilder("")
        )
        self.assertIsNotNone(some_trigger.apply_on(DummyState(), 1))
        self.assertIsNone(some_trigger.apply_on(DummyState(1), 1))


if __name__ == "__main__":
    unittest.main()
