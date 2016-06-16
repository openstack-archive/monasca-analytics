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

from monasca_analytics.source.markov_chain import state_check as sc


class MarkovChain(object):
    """Possible transitions for each state.

    This class describes the possible transitions for
    a particular type of state.
    It can use the dependencies of the node as it want.
    """

    def __init__(self, transitions):
        self._transitions = dict()
        for tr in transitions:
            from_state = tr.from_state()
            if from_state in self._transitions:
                self._transitions[from_state].append(tr)
            else:
                self._transitions[from_state] = [tr]

    def apply_on(self, node, hour_of_day):
        """Performs a state transition for the given node.

        :type node: monasca_analytics.source.markov_chain.base.StateNode
        :param node: the state of this node will be changed
        :type hour_of_day: int
        :param hour_of_day: the hour of the day (used by probability checks)
        :rtype: bool
        :returns: True if there exists in the model at least one transition
                  from the node current state.
        """
        if node.state not in self._transitions:
            return False
        for tr in self._transitions[node.state]:
            if tr(node, hour_of_day):
                break
        return True


class Transition(object):
    """Holds requirement for a transition

    This function object holds the requirement for effectively
    performing a transition on a node. It assumes to be used
    only by the MarkovChain class who make sure that the node
    has the proper state before applying the transition.
    """

    def __init__(self, from_state, to_state, prob_check, deps_check=None):
        """Create a new Transition instance.

        :param from_state: precondition for the node. It must be in this
        state in order to have a chance to be promoted into `to_state`
        :param to_state: next state if the condition is met.
        :param prob_check: the markov condition.
        :param deps_check: deterministic check performed on dependencies.
        """
        self._from_state = from_state
        self._to_state = to_state
        if deps_check is not None:
            self._deps_check = sc.DepCheck(deps_check)
        else:
            self._deps_check = sc.TrueCheck()
        self._prob_check = prob_check

    def __call__(self, node, hour_of_day):
        if self._prob_check(hour_of_day) and\
                self._deps_check(node) and\
                self._from_state == node.state:
            node.state = self._to_state
            return True
        return False

    def from_state(self):
        return self._from_state
