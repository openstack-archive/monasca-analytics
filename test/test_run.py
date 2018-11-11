#!/usr/bin/env python

# Copyright (c) 2018 FUJITSU LIMITED
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

import run
from test.util_for_testing import MonanasTestCase


class ParserTest(MonanasTestCase):
    """Test argment parser in run.py"""

    def setUp(self):
        super(ParserTest, self).setUp()
        self.parser = run.setup_parser()

    def tearDown(self):
        super(ParserTest, self).tearDown()

    def _get_parser(self, args):
        try:
            parsed = self.parser.parse_args(args)
        except SystemExit:
            raise ParserException("Argument parse failed")

        return parsed

    def _check_parser(self, parsed, args, verify_args):
        for av in verify_args:
            attr, value = av
            if attr:
                self.assertIn(attr, parsed)
                self.assertEqual(value, getattr(parsed, attr))

    def test_parser_required(self):
        arglist = [
            '--config', '/path/to/config_file',
            '--log_config', '/path/to/log_file',
            '--spark_path', '/path/to/spark',
        ]

        verifylist = [
            ('config', '/path/to/config_file'),
            ('log_config', '/path/to/log_file'),
            ('spark_path', '/path/to/spark'),
        ]

        parsed = self._get_parser(arglist)
        self._check_parser(parsed, arglist, verifylist)

    def test_parser_optional(self):
        arglist = [
            '--config', '/path/to/config_file',
            '--log_config', '/path/to/log_file',
            '--spark_path', '/path/to/spark',
            '--sources', '/path/to/src1', '/path/to/src2',
        ]

        verifylist = [
            ('config', '/path/to/config_file'),
            ('log_config', '/path/to/log_file'),
            ('spark_path', '/path/to/spark'),
            ('sources', ['/path/to/src1', '/path/to/src2']),
        ]

        parsed = self._get_parser(arglist)
        self._check_parser(parsed, arglist, verifylist)

    def test_parser_optional_bool(self):
        arglist = [
            '--config', '/path/to/config_file',
            '--log_config', '/path/to/log_file',
            '--spark_path', '/path/to/spark',
            '--debug',
        ]

        parsed = self._get_parser(arglist)
        self.assertTrue(parsed.debug)
