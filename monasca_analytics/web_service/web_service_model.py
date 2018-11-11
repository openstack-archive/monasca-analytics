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

"""A list of functions to validate web_service models."""

import voluptuous


import six


def action_model(value):
    """Validates the data against action_model schema."""
    action_model_schema = voluptuous.Schema({
        "action": voluptuous.And(six.string_types[0],
                                 lambda o: not o.startswith("_"))
    }, required=True)

    return action_model_schema(value)


def banana_model(value):
    """Validates the data against the banana_model schema."""
    banana_model_schema = voluptuous.Schema({
        "content": six.string_types[0]
    }, required=True)

    return banana_model_schema(value)
