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
import re

import monasca_analytics.banana.pass_manager as p
import monasca_analytics.exception.banana as exception
from test.util_for_testing import MonanasTestCase


logger = logging.getLogger(__name__)

_has_some_file_that_should = dict()
_has_some_file_that_should["pass"] = False
_has_some_file_that_should["fail"] = False


class TypecheckTestCase(MonanasTestCase):

    def setUp(self):
        super(TypecheckTestCase, self).setUp()

    def tearDown(self):
        super(TypecheckTestCase, self).tearDown()

    def test_files_have_been_found(self):
        self.assertTrue(_has_some_file_that_should["pass"])
        self.assertTrue(_has_some_file_that_should["fail"])


def upgrade_test_case():
    regex_pass = re.compile("#(?: )*TYPE_TABLE_EQ(?: )*([^\n]+)")
    regex_fail = re.compile("#(?: )*RAISE(?: )*([^\n]+)")
    regex_split = re.compile("#(?: )*NEW_TEST(?:[^\n]*)\n")

    for root, dirs, files in os.walk('./banana/typeck/should_pass'):
        for filename in files:
            name_no_ext, _ = os.path.splitext(filename)
            _has_some_file_that_should["pass"] = True
            with open(os.path.join(root, filename), 'r') as f:
                content = f.read()
                expect_type_table = regex_pass.search(content)
                if expect_type_table is not None:
                    expect_type_table = expect_type_table.group(1)

                def create_test(test_str, expected_type_table):
                    def should_pass(self):
                        type_table = p.compute_type_table(test_str)
                        if expected_type_table is not None:
                            self.assertEqual(str(type_table),
                                             expected_type_table)
                        else:
                            raise Exception(
                                "Missing # TYPE_TABLE_EQ <...> in test."
                            )

                    should_pass.__name__ = "test_banana_pass_" + name_no_ext
                    return should_pass

                many_tests = regex_split.split(content)
                if len(many_tests) == 1:
                    setattr(TypecheckTestCase,
                            "test_banana_pass_" + name_no_ext,
                            create_test(many_tests[0], expect_type_table))
                else:
                    suffix = 0
                    for test_case in many_tests:
                        suffix += 1
                        setattr(TypecheckTestCase,
                                "test_banana_pass_" + name_no_ext +
                                str(suffix),
                                create_test(test_case, expect_type_table))

    for root, dirs, files in os.walk('./banana/typeck/should_fail'):
        for filename in files:
            name_no_ext, _ = os.path.splitext(filename)
            _has_some_file_that_should["fail"] = True
            with open(os.path.join(root, filename), 'r') as f:
                content = f.read()
                expect_error = regex_fail.search(content)
                if expect_error is not None:
                    expect_error = expect_error.group(1)

                def create_test(s, test_str, expected_error):
                    def should_fail(self):
                        if expected_error is not None:
                            expected_exception = get_exception_from_str(
                                expected_error)
                            self.assertRaises(
                                expected_exception,
                                p.compute_type_table,
                                test_str)
                        else:
                            raise Exception("Missing # RAISE in test")
                    should_fail.__name__ = "test_banana_fail_" + name_no_ext +\
                                           str(s)
                    return should_fail

                many_tests = regex_split.split(content)
                if len(many_tests) == 1:
                    setattr(TypecheckTestCase,
                            "test_banana_fail_" + name_no_ext,
                            create_test("", many_tests[0], expect_error))
                else:
                    suffix = 0
                    for test_case in many_tests:
                        suffix += 1
                        setattr(TypecheckTestCase,
                                "test_banana_fail_" + name_no_ext +
                                str(suffix),
                                create_test(suffix, test_case, expect_error))

# Fill the test case with generated test case from banana files
upgrade_test_case()


def get_exception_from_str(string):
    if string == exception.BananaAssignCompError.__name__:
        return exception.BananaAssignCompError
    if string == exception.BananaConnectionError.__name__:
        return exception.BananaConnectionError
    if string == exception.BananaAssignmentError.__name__:
        return exception.BananaAssignmentError
    if string == exception.BananaTypeError.__name__:
        return exception.BananaTypeError
    if string == exception.BananaArgumentTypeError.__name__:
        return exception.BananaArgumentTypeError
    if string == exception.BananaUnknown.__name__:
        return exception.BananaUnknown
    if string == exception.BananaPropertyDoesNotExists.__name__:
        return exception.BananaPropertyDoesNotExists
    if string == exception.BananaComponentIncorrectParamName.__name__:
        return exception.BananaComponentIncorrectParamName
    if string == exception.BananaComponentTooManyParams.__name__:
        return exception.BananaComponentTooManyParams
    if string == exception.BananaShadowingComponentError.__name__:
        return exception.BananaShadowingComponentError
    if string == exception.BananaUnknownOperator.__name__:
        return exception.BananaUnknownOperator
    raise Exception("Invalid exception name: '{}'".format(string))
