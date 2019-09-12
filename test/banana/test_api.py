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

from monasca_analytics.exception.banana import BananaEnvironmentError
from monasca_analytics.exception.banana import BananaInvalidExpression
from monasca_analytics.parsing.api import validate_environment
from monasca_analytics.parsing.api import validate_expression
from monasca_analytics.parsing.api import validate_name_binding
from test.util_for_testing import MonanasTestCase


class TestBananaAPI(MonanasTestCase):

    def setUp(self):
        super(TestBananaAPI, self).setUp()

    def tearDown(self):
        super(TestBananaAPI, self).tearDown()

    def test_validate_expression_is_valid(self):
        validate_expression("a + b")
        validate_expression("a * b")
        validate_expression("a - b")
        validate_expression("a / b")
        validate_expression("a / b + 12 * (1 - a)")

    def test_validate_expression_is_invalid(self):
        self.assertRaises(BananaInvalidExpression, validate_expression,
                          "a123")
        self.assertRaises(BananaInvalidExpression, validate_expression,
                          "a n + 15")
        self.assertRaises(BananaInvalidExpression, validate_expression,
                          "a * exp(b)")
        self.assertRaises(BananaInvalidExpression, validate_expression,
                          "-a")
        self.assertRaises(BananaInvalidExpression, validate_expression,
                          "- a")
        self.assertRaises(BananaInvalidExpression, validate_expression,
                          "+ b")

    def test_validate_name_binding_is_valid(self):
        validate_name_binding(
            validate_expression("a + b * c"),
            {"a": "foo", "b": "foo", "c": "bar"}
        )

    def test_validate_name_binding_is_invalid(self):
        self.assertRaises(BananaInvalidExpression,
                          validate_name_binding,
                          validate_expression("a + b * c"),
                          {"a": "foo", "c": "bar"})

    def test_validate_environment_is_valid(self):
        validate_environment({"a": "foo", "c": "bar"})

    def test_validate_environment_is_invalid(self):
        self.assertRaises(BananaEnvironmentError,
                          validate_environment, {"a": 0})
