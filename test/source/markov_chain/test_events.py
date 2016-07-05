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

import datetime

import monasca_analytics.source.markov_chain.events as ev
import monasca_analytics.source.markov_chain.prob_checks as pck
import monasca_analytics.source.markov_chain.state_check as dck
import test.mocks.markov as markov_mocks

from test.util_for_testing import MonanasTestCase


class DummyState(object):

    def __init__(self, state=0):
        self.state = state
        self.dependencies = []

    def id(self):
        return 0


class TriggersTest(MonanasTestCase):

    def setUp(self):
        super(TriggersTest, self).setUp()

    def tearDown(self):
        super(TriggersTest, self).tearDown()

    def test_trigger_should_create_event_when_necessary(self):
        some_trigger = ev.Trigger(
            node_check=dck.EqCheck(0),
            prob_check=pck.NoProbCheck(),
            event_builder=ev.EventBuilder("")
        )
        events = []
        some_trigger.apply_on(
            DummyState(),
            1,
            datetime.datetime.now(),
            markov_mocks.MockRequestBuilder(events))
        self.assertEqual(len(events), 1)
        events = []
        some_trigger.apply_on(
            DummyState(1),
            1,
            datetime.datetime.now(),
            markov_mocks.MockRequestBuilder(events))
        self.assertEqual(len(events), 0)
