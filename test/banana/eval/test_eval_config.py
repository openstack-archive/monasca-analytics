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

from monasca_analytics.banana.pass_manager import compute_evaluation_context
from monasca_analytics.util.string_util import stable_repr
from test.util_for_testing import MonanasTestCase


logger = logging.getLogger(__name__)

_has_some_file_that_should = dict()
_has_some_file_that_should["pass_eval_stmt"] = False


class EvalTestCase(MonanasTestCase):

    def setUp(self):
        super(EvalTestCase, self).setUp()

    def tearDown(self):
        super(EvalTestCase, self).tearDown()

    def test_files_have_been_found(self):
        self.assertTrue(_has_some_file_that_should["pass_eval_stmt"])


def upgrade_test_case():
    regex_var_eq = re.compile("#(?: )*LHS_EQ(?: )+([^\n]+)")

    for root, dirs, files in os.walk('./banana/eval/should_pass/'):
        for filename in files:
            name_no_ext, _ = os.path.splitext(filename)
            _has_some_file_that_should["pass_eval_stmt"] = True
            with open(os.path.join(root, filename), 'r') as f:
                content = f.read()

                expected_values = regex_var_eq.findall(content)

                def create_test(test_str, expect_values):
                    def should_pass(self):
                        # Custom checks runned after each statement
                        box = {"counter": 0}

                        def custom_check(ctx, stmt_type, lhs_node, rhs_value):
                            if expect_values[box["counter"]] != "IGNORE":
                                self.assertEqual(
                                    expect_values[box["counter"]],
                                    stable_repr(rhs_value))
                            box["counter"] += 1
                        # Evaluate the file.
                        compute_evaluation_context(test_str, custom_check)

                    should_pass.__name__ = "test_banana_eval_" + name_no_ext
                    return should_pass

                setattr(EvalTestCase, "test_banana_eval_" + name_no_ext,
                        create_test(content, expected_values))

# Fill the test case with generated test case from banana files
upgrade_test_case()
