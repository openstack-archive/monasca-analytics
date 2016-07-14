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
import os
import pyparsing as p
import re

from monasca_analytics.banana.grammar.config import banana_grammar
from test.util_for_testing import MonanasTestCase


logger = logging.getLogger(__name__)

_has_some_file_that_should = dict()
_has_some_file_that_should["pass"] = False
_has_some_file_that_should["fail"] = False


class GrammarTestCase(MonanasTestCase):

    def setUp(self):
        super(GrammarTestCase, self).setUp()

    def tearDown(self):
        super(GrammarTestCase, self).tearDown()

    def test_files_have_been_found(self):
        self.assertTrue(_has_some_file_that_should["pass"])
        self.assertTrue(_has_some_file_that_should["fail"])


def upgrade_test_case():
    grammar = banana_grammar()
    regex_raise = re.compile("#(?: )*RAISE(?: )*([^\n]+)")
    regex_ast_eq = re.compile("#(?: )*AST_EQ(?: )(?: )*([^\n]+)")
    regex_stmt_eq = re.compile("#(?: )*STMT_EQ(?: )(?: )*([^\n]+)")
    regex_conn_eq = re.compile("#(?: )*CONN_EQ(?: )(?: )*([^\n]+)")

    for root, dirs, files in os.walk('./banana/grammar/should_pass'):
        for filename in files:
            name_no_ext, _ = os.path.splitext(filename)
            _has_some_file_that_should["pass"] = True
            with open(os.path.join(root, filename), 'r') as f:
                content = f.read()

                expected_ast = regex_ast_eq.search(content)
                if expected_ast is not None:
                    expected_ast = expected_ast.group(1)
                expected_stmt = regex_stmt_eq.search(content)
                if expected_stmt is not None:
                    expected_stmt = expected_stmt.group(1)
                expected_conn = regex_conn_eq.search(content)
                if expected_conn is not None:
                    expected_conn = expected_conn.group(1)

                def create_test(test_str, expect_ast, expect_stmt, exp_conn):
                    def should_pass(self):
                        tree = grammar.parse(test_str)
                        if expect_ast is not None:
                            self.assertEqual(str(tree),
                                             expect_ast)
                        if expect_stmt is not None:
                            self.assertEqual(tree.statements_to_str(),
                                             expect_stmt)
                        if exp_conn is not None:
                            self.assertEqual(str(tree.connections),
                                             exp_conn)
                        if exp_conn is None and expect_ast is None and\
                           expect_stmt is None:
                            raise Exception("Expected at least one check!")

                    should_pass.__name__ = "test_banana_pass_" + name_no_ext
                    return should_pass

                setattr(GrammarTestCase, "test_banana_pass_" + name_no_ext,
                        create_test(content, expected_ast, expected_stmt,
                                    expected_conn))

    for root, dirs, files in os.walk('./banana/grammar/should_fail'):
        for filename in files:
            name_no_ext, _ = os.path.splitext(filename)
            _has_some_file_that_should["fail"] = True
            with open(os.path.join(root, filename), 'r') as f:
                content = f.read()

                def create_test(test_str):
                    def should_fail(self):
                        expected_error = regex_raise.search(test_str).group(1)
                        expected_exception = get_exception_from_str(
                            expected_error)
                        self.assertRaises(
                            expected_exception,
                            grammar.parse,
                            test_str)
                    should_fail.__name__ = "test_banana_fail_" + name_no_ext
                    return should_fail

                setattr(GrammarTestCase, "test_banana_fail_" + name_no_ext,
                        create_test(content))

# Fill the test case with generated test case from banana files
upgrade_test_case()


def get_exception_from_str(string):
    if string == p.ParseSyntaxException.__name__:
        return p.ParseSyntaxException
    if string == p.ParseFatalException.__name__:
        return p.ParseFatalException
    if string == p.ParseException.__name__:
        return p.ParseException
    raise Exception("Invalid exception name: '{}'".format(string))
