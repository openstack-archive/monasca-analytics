#!/usr/bin/env python

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
