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

import monasca_analytics.banana.emitter as emit
import monasca_analytics.banana.pass_manager as p

from test.util_for_testing import MonanasTestCase


logger = logging.getLogger(__name__)

_has_some_examples_been_found = {0: False}


class ConfigExamplesTestCase(MonanasTestCase):

    def setUp(self):
        super(ConfigExamplesTestCase, self).setUp()

    def tearDown(self):
        super(ConfigExamplesTestCase, self).tearDown()

    def test_files_has_been_found(self):
        self.assertTrue(_has_some_examples_been_found[0])


def upgrade_test_case():
    for root, dirs, files in os.walk('../config'):
        for filename in files:
            name_no_ext, ext = os.path.splitext(filename)
            if ext == '.banana':
                _has_some_examples_been_found[0] = True
                with open(os.path.join(root, filename), 'r') as f:
                    content = f.read()

                    def create_test(test_str):
                        def should_pass(self):
                            fake_driver = FakeDriver()
                            emitter = CustomEmitter()
                            p.execute_banana_string(
                                test_str, fake_driver, emitter)
                            self.assertEqual(emitter.nb_errors, 0)
                            self.assertEqual(emitter.nb_warnings, 0)
                            self.assertTrue(fake_driver.set_links_called)
                            self.assertTrue(fake_driver.start_pipeline_called)
                            self.assertTrue(fake_driver.stop_pipeline_called)

                        should_pass.__name__ = "test_banana_examples_config"
                        return should_pass

                    setattr(ConfigExamplesTestCase,
                            "test_banana_examples_config_" + name_no_ext,
                            create_test(content))

upgrade_test_case()


class FakeDriver(object):

    def __init__(self):
        self.start_pipeline_called = False
        self.stop_pipeline_called = False
        self.set_links_called = False

    def stop_pipeline(self):
        self.stop_pipeline_called = True

    def start_pipeline(self):
        self.start_pipeline_called = True

    def set_links(self, _):
        self.set_links_called = True


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
