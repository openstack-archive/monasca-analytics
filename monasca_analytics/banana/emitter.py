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

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class Emitter(object):
    """
    Emitter base class to emit errors and warnings.
    Typically errors will be collected and then send
    over the network as an http response but for tests
    and debugging, a `PrintEmitter` can be used instead.
    """

    @abc.abstractmethod
    def emit_warning(self, span, message):
        """
        Emit a warning.
        :type span: monasca_analytics.banana.grammar.base_ast.Span
        :param span: Span associated with the message.
        :type message: str
        :param message: message to emit with the warning level.
        """
        pass

    @abc.abstractmethod
    def emit_error(self, span, message):
        """
        Emit an error
        :type span: monasca_analytics.banana.grammar.base_ast.Span
        :param span: Span associated with the message.
        :type message: str
        :param message: message to emit with the error level.
        """
        pass


class PrintEmitter(Emitter):
    """
    Print warnings and errors to the console.
    """
    def emit_warning(self, span, message):
        print("WARNING at line:{}".format(span.get_lineno()))
        print("WARNING: {}".format(message))

    def emit_error(self, span, message):
        print("ERROR at line:{}".format(span.get_lineno()))
        print("ERROR: {}".format(message))


class JsonEmitter(Emitter):
    """
    Print warnings and errors in a Json object.
    """
    def __init__(self):
        self.result = {
            "errors": [],
            "warnings": [],
        }

    def emit_error(self, span, message):
        error = JsonEmitter._gen_message_structure(span, message)
        self.result["errors"].append(error)

    def emit_warning(self, span, message):
        warning = JsonEmitter._gen_message_structure(span, message)
        self.result["warnings"].append(warning)

    @staticmethod
    def _gen_message_structure(span, message):
        spanrange = span.get_range()
        return {
            "startLineNumber": spanrange[0][0],
            "startColumn": spanrange[0][1],
            "endLineNumber": spanrange[1][0],
            "endColumn": spanrange[1][1],
            "byteRange": [span.lo, span.hi],
            "message": message
        }
