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

"""Monanas Error classes."""

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class MonanasException(Exception):

    @abc.abstractmethod
    def __str__(self):
        pass


class MonanasMainError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasInitError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasBindSourcesError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasAlreadyStartedStreaming(MonanasException):
    def __init__(self):
        self._value = "Monanas has already started streaming."

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasAlreadyStoppedStreaming(MonanasException):
    def __init__(self):
        self._value = "Monanas has already stopped streaming."

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasStreamingError(MonanasException):
    def __init__(self):
        self._value = "Unable to start streaming data. Make sure there is at \
            least one operation registered."

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasNoSuchClassError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasDuplicateClassError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasNoSuchSourceError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasDuplicateSourceError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasNoSuchIngestorError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasDuplicateIngestorError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasNoSuchAggregatorError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasDuplicateAggregatorError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasNoSuchSMLError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasDuplicateSMLError(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasDStreamNotReady(MonanasException):
    def __init__(self):
        self._value = "The dstream requested is not ready."

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasAlreadyIngested(MonanasException):
    def __init__(self):
        self._value = "Monanas has already ingested data."

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasNoSuchSourceModel(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasInvalidConfig(MonanasException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        MonanasException.__str__(self)
        return repr(self._value)


class MonanasCyclicRandomSourceError(Exception):

    def __init__(self):
        self._value = "Monanas couldn't start the linearly dependent \
            random source: Cycle found."

    def __str__(self):
        return repr(self._value)


class MonanasWrongConnectoinError(Exception):

    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)
