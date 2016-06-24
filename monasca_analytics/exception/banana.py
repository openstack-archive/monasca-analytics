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

"""Banana Error classes."""

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BananaException(Exception):

    @abc.abstractmethod
    def __str__(self):
        pass


class BananaInvalidExpression(BananaException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)


class BananaEnvironmentError(BananaException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)


class BananaArgumentTypeError(BananaException):
    def __init__(self, expected_type, received_type):
        self._value = "Wrong type of argument: expected '{}' got '{}'".\
            format(expected_type.__name__, received_type.__name__)

    def __str__(self):
        return repr(self._value)
