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
import monasca_analytics.banana.emitter as emit
import monasca_analytics.banana.grammar.config as grammar
import monasca_analytics.banana.typeck.config as typeck

from test.util_for_testing import MonanasTestCase

logger = logging.getLogger(__name__)


class DeadPathTestCase(MonanasTestCase):

    def setUp(self):
        super(DeadPathTestCase, self).setUp()

    def tearDown(self):
        super(DeadPathTestCase, self).tearDown()

    def test_banana_should_remove_everything(self):
        banana_str = "" +\
            "a = CloudMarkovChainSource()\n" +\
            "b = StdoutSink()\n" +\
            "c = CloudIngestor()\n" +\
            "d = LiNGAM()\n" +\
            "a -> c -> d"
        emitter = CustomEmitter()
        # Convert the grammar into an AST
        parser = grammar.banana_grammar(emitter)
        ast = parser.parse(banana_str)
        # Compute the type table for the given AST
        type_table = typeck.typeck(ast)
        # Remove from the tree path that are "dead"
        deadpathck.deadpathck(ast, type_table, emitter)
        self.assertEqual(emitter.nb_errors, 0)
        self.assertEqual(emitter.nb_warnings, 4)
        self.assertEqual(len(ast.components), 0)
        self.assertEqual(len(ast.connections.connections), 0)

    def test_banana_should_remove_one(self):
        banana_str = "" +\
            "a = CloudMarkovChainSource()\n" +\
            "b = StdoutSink()\n" +\
            "c = CloudIngestor()\n" +\
            "d = LiNGAM()\n" +\
            "a -> c -> [d, b]"
        emitter = CustomEmitter()
        # Convert the grammar into an AST
        parser = grammar.banana_grammar(emitter)
        ast = parser.parse(banana_str)
        # Compute the type table for the given AST
        type_table = typeck.typeck(ast)
        # Remove from the tree path that are "dead"
        deadpathck.deadpathck(ast, type_table, emitter)
        self.assertEqual(emitter.nb_errors, 0)
        self.assertEqual(emitter.nb_warnings, 1)
        self.assertEqual(len(ast.components), 3)
        self.assertEqual(len(ast.connections.connections), 2)

    def test_banana_should_not_remove_anything(self):
        banana_str = "" +\
            "a = CloudMarkovChainSource()\n" +\
            "b = StdoutSink()\n" +\
            "c = CloudIngestor()\n" +\
            "d = LiNGAM()\n" +\
            "a -> c -> d -> b"
        emitter = CustomEmitter()
        # Convert the grammar into an AST
        parser = grammar.banana_grammar(emitter)
        ast = parser.parse(banana_str)
        # Compute the type table for the given AST
        type_table = typeck.typeck(ast)
        # Remove from the tree path that are "dead"
        deadpathck.deadpathck(ast, type_table, emitter)
        self.assertEqual(emitter.nb_errors, 0)
        self.assertEqual(emitter.nb_warnings, 0)
        self.assertEqual(len(ast.components), 4)
        self.assertEqual(len(ast.connections.connections), 3)


class CustomEmitter(emit.Emitter):

    def __init__(self):
        super(CustomEmitter, self).__init__()
        self.nb_warnings = 0
        self.nb_errors = 0

    def emit_warning(self, span, message):
        print(span.get_line(), str(span), message)
        self.nb_warnings += 1

    def emit_error(self, span, message):
        print(span.get_line(), str(span), message)
        self.nb_errors += 1
