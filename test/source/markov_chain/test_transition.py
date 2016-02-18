#!/usr/bin/env python

import json
import logging
import os
import unittest

import main.source.markov_chain.prob_checks as pck
import main.source.markov_chain.state_check as dck
import main.source.markov_chain.transition as t


class DummyState(object):

    def __init__(self, state=0):
        self.state = state
        self.dependencies = []


class MarkovChainTransitionsTest(unittest.TestCase):

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

    def test_first_order_dep_check(self):
        state = DummyState()
        state.dependencies.append(DummyState(1))
        dc = dck.DepCheck(dck.EqCheck(1))
        self.assertTrue(dc(state))
        state = DummyState()
        self.assertFalse(dc(state))
        state = DummyState()
        state.dependencies.append(DummyState(2))
        self.assertFalse(dc(state))

    def test_second_order_dep_check(self):
        state = DummyState()
        state1 = DummyState()
        state.dependencies.append(state1)
        state1.dependencies.append(DummyState(1))
        dc = dck.DepCheck(dck.DepCheck(dck.EqCheck(1)))
        self.assertTrue(dc(state))
        state = DummyState()
        self.assertFalse(dc(state))
        self.assertFalse(dc(state1))

    def test_combiner_and_dep_check(self):
        state = DummyState()
        state1 = DummyState(1)
        state.dependencies.append(state1)
        state1.dependencies.append(DummyState(2))
        dc = dck.AndCheck(c1=dck.DepCheck(dck.EqCheck(1)),
                          c2=dck.DepCheck(dck.DepCheck(dck.EqCheck(2))))
        self.assertTrue(dc(state))
        self.assertFalse(dc(state1))
        state1.state = 2
        self.assertFalse(dc(state))
        state1.state = 1
        state1.dependencies[0].state = 1
        self.assertFalse(dc(state))
        state = DummyState()
        self.assertFalse(dc(state))

    def test_combiner_or_dep_check(self):
        state = DummyState()
        state1 = DummyState(1)
        state.dependencies.append(state1)
        state1.dependencies.append(DummyState(2))
        dc = dck.OrCheck(c1=dck.DepCheck(dck.EqCheck(1)),
                         c2=dck.DepCheck(dck.DepCheck(dck.EqCheck(2))))
        self.assertTrue(dc(state))
        self.assertFalse(dc(state1))
        state1.dependencies[0].state = 1
        self.assertTrue(dc(state))
        self.assertTrue(dc(state1))
        state1.state = 2
        self.assertFalse(dc(state))
        state = DummyState()
        self.assertFalse(dc(state))

    def test_prob_check(self):
        pc = pck.ProbCheck(0.5)
        i = 0
        while i < 30:
            if pc(0):
                break
            i += 1
        self.assertTrue(i < 30)

    def test_prob_check_interpolate(self):
        pc = pck.ProbCheck({0: 0.0, 1: 0.0, 24: 1.0})
        self.assertFalse(pc(0))
        self.assertFalse(pc(1))
        self.assertTrue(pc(24))
        i = 0
        while i < 30:
            if pc(12):
                break
            i += 1
        self.assertTrue(i < 30)

    def test_transition(self):
        tr = t.Transition(0, 1, pck.ProbCheck(1.0))
        state = DummyState(0)
        self.assertTrue(tr(state, 1))
        self.assertEqual(state.state, 1)
        state = DummyState(2)
        self.assertFalse(tr(state, 1))
        self.assertEqual(state.state, 2)

    def test_transition_with_true_check(self):
        tr = t.Transition(0, 1, pck.NoProbCheck(), dck.TrueCheck())
        state = DummyState(0)
        self.assertFalse(tr(state, 1))
        state1 = DummyState(123456)
        state.dependencies.append(state1)
        self.assertTrue(tr(state, 1))
        self.assertEqual(state.state, 1)

    def test_markov_chain(self):
        tr1 = t.Transition(0, 1, pck.ProbCheck(1.0))
        tr2 = t.Transition(1, 2, pck.ProbCheck(1.0))
        mc = t.MarkovChain([tr1, tr2])
        state1 = DummyState(0)
        state2 = DummyState(1)
        mc.apply_on(state1, 1)
        mc.apply_on(state2, 1)
        self.assertEqual(state1.state, 1)
        self.assertEqual(state2.state, 2)
        mc.apply_on(state1, 1)
        mc.apply_on(state2, 1)
        self.assertEqual(state1.state, 2)
        self.assertEqual(state2.state, 2)


if __name__ == "__main__":
    unittest.main()
