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

import logging

import monasca_analytics.banana.deadpathck.config as deadpathck
import monasca_analytics.banana.grammar.config as grammar
import monasca_analytics.banana.typeck.config as typeck
import monasca_analytics.exception.banana as exception

from test.util_for_testing import MonanasTestCase

logger = logging.getLogger(__name__)


class PassOneSinkSourceTestCase(MonanasTestCase):

    def setUp(self):
        super(PassOneSinkSourceTestCase, self).setUp()

    def tearDown(self):
        super(PassOneSinkSourceTestCase, self).tearDown()

    def test_banana_should_fail_when_no_source(self):
        banana_str = "" +\
            "a = CloudMarkovChainSource()\n" +\
            "b = StdoutSink()\n" +\
            "c = CloudIngestor()\n" +\
            "d = LiNGAM()\n" +\
            "c -> d -> b"
        # Convert the grammar into an AST
        parser = grammar.banana_grammar()
        ast = parser.parse(banana_str)
        # Compute the type table for the given AST
        type_table = typeck.typeck(ast)
        # Remove from the tree path that are "dead"
        deadpathck.deadpathck(ast, type_table)
        self.assertRaises(
            exception.BananaNoFullPath,
            deadpathck.contains_at_least_one_path_to_a_sink,
            ast,
            type_table
        )

    def test_banana_should_fail_when_no_sink(self):
        banana_str = "" +\
            "a = CloudMarkovChainSource()\n" +\
            "b = StdoutSink()\n" +\
            "c = CloudIngestor()\n" +\
            "d = LiNGAM()\n" +\
            "a -> c -> d"
        # Convert the grammar into an AST
        parser = grammar.banana_grammar()
        ast = parser.parse(banana_str)
        # Compute the type table for the given AST
        type_table = typeck.typeck(ast)
        # Remove from the tree path that are "dead"
        deadpathck.deadpathck(ast, type_table)
        self.assertRaises(
            exception.BananaNoFullPath,
            deadpathck.contains_at_least_one_path_to_a_sink,
            ast,
            type_table
        )

    def test_banana_should_pass_when_more_source_sink(self):
        banana_str = "" +\
            "a = CloudMarkovChainSource()\n" +\
            "b = StdoutSink()\n" +\
            "c = CloudIngestor()\n" +\
            "d = LiNGAM()\n" +\
            "a -> c -> d -> b"
        # Convert the grammar into an AST
        parser = grammar.banana_grammar()
        ast = parser.parse(banana_str)
        # Compute the type table for the given AST
        type_table = typeck.typeck(ast)
        # Remove from the tree path that are "dead"
        deadpathck.deadpathck(ast, type_table)
        deadpathck.contains_at_least_one_path_to_a_sink(ast, type_table)
        # We should reach this line.
        self.assertTrue(True)
