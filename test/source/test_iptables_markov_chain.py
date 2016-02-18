import json
import logging
import os
import unittest

import schema

from main.source import iptables_markov_chain


class TestIPTablesSource(unittest.TestCase):

    def setup_logging(self):
        current_dir = os.path.dirname(__file__)
        logging_config_file = os.path.join(current_dir,
                                           "../resources/logging.json")
        with open(logging_config_file, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    def setUp(self):
        self.setup_logging()
        self.valid_config = {
            "module": "IPTablesSource",
            "params": {
                "server_sleep_in_seconds": 0.01
            }
        }
        self.config_extra_param = {
            "module": "IPTablesSource",
            "params": {
                "server_sleep_in_seconds": 0.01,
                "infiltrated": "wrong_param"
            }
        }
        self.config_missing_param = {
            "module": "IPTablesSource",
            "params": {}
        }
        self.config_wrong_type = {
            "module": "IPTablesSource",
            "params": {
                "server_sleep_in_seconds": "I should be an integer"
            }
        }
        self.config_missing_params = {"module": "IPTablesSource"}
        self.ips = iptables_markov_chain.IPTablesSource("fake_id",
                                                        self.valid_config)

    def tearDown(self):
        pass

    def test_validate_valid_config(self):
        self.assertEqual(self.valid_config, self.ips._config)

    def test_validate_config_extra_param(self):
        self.assertRaises(
            schema.SchemaError, self.ips.validate_config,
            self.config_extra_param)

    def test_validate_config_missing_param(self):
        self.assertRaises(
            schema.SchemaError, self.ips.validate_config,
            self.config_missing_param)

    def test_validate_config_wrong_type(self):
        self.assertRaises(
            schema.SchemaError,
            self.ips.validate_config,
            self.config_wrong_type)

    def test_get_default_config(self):
        default_config = iptables_markov_chain.\
            IPTablesSource.get_default_config()
        iptables_markov_chain.IPTablesSource.validate_config(default_config)
        self.assertEqual("IPTablesSource", default_config["module"])

    def assertStateNode(self, node, state, num_triggers, states_transitions):
        self.assertEqual(node.state, state)
        self.assertEqual(len(node._triggers), num_triggers)
        self.assertEqual(len(node._markov_chain._transitions),
                         len(states_transitions.keys()))
        for state, num_transitions in states_transitions.iteritems():
            self.assertEqual(len(node._markov_chain._transitions[state]),
                             num_transitions)

    def assertTransition(self, transition, from_state, to_state):
        self.assertEqual(transition._from_state, from_state)
        self.assertEqual(transition._to_state, to_state)

    def assert_all_correct_transitions(self, trs):
        self.assertTransition(trs[iptables_markov_chain.STATE_STOP][0],
                              from_state=iptables_markov_chain.STATE_STOP,
                              to_state=iptables_markov_chain.STATE_NORMAL)
        self.assertTransition(trs[iptables_markov_chain.STATE_NORMAL][0],
                              from_state=iptables_markov_chain.STATE_NORMAL,
                              to_state=iptables_markov_chain.STATE_STOP)
        self.assertTransition(trs[iptables_markov_chain.STATE_NORMAL][1],
                              from_state=iptables_markov_chain.STATE_NORMAL,
                              to_state=iptables_markov_chain.STATE_ATTACK)
        self.assertTransition(trs[iptables_markov_chain.STATE_ATTACK][0],
                              from_state=iptables_markov_chain.STATE_ATTACK,
                              to_state=iptables_markov_chain.STATE_NORMAL)

    def test_create_system(self):
        nodes = self.ips._create_system()
        self.assertEqual(1, len(nodes))
        self.assertStateNode(nodes[0],
                             state=iptables_markov_chain.STATE_STOP,
                             num_triggers=16,
                             states_transitions={
                                iptables_markov_chain.STATE_STOP: 1,
                                iptables_markov_chain.STATE_NORMAL: 2,
                                iptables_markov_chain.STATE_ATTACK: 1
                            })
        self.assert_all_correct_transitions(nodes[0].
                                            _markov_chain._transitions)

    def test_create_markov_chain_model(self):
        markov_chain = self.ips._create_markov_chain_model()
        self.assert_all_correct_transitions(markov_chain._transitions)
