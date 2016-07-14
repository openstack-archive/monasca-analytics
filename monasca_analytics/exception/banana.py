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
import pyparsing as p
import six

import monasca_analytics.banana.grammar.base_ast as ast


@six.add_metaclass(abc.ABCMeta)
class BananaException(Exception):

    @abc.abstractmethod
    def __str__(self):
        pass

    @abc.abstractmethod
    def get_span(self):
        """
        :rtype: ast.Span
        :return: Returns the span where the error occured if appropriate
        """
        pass


class BananaInvalidExpression(BananaException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)

    def get_span(self):
        return ast.DUMMY_SPAN


class BananaEnvironmentError(BananaException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)

    def get_span(self):
        return ast.DUMMY_SPAN


class BananaNoFullPath(BananaException):
    def __init__(self, missing):
        self._value = "None of the paths can be executed. Missing at least" \
                      " one {}.".format(missing)

    def __str__(self):
        return self._value

    def get_span(self):
        return ast.DUMMY_SPAN


class BananaArgumentTypeError(BananaException):
    def __init__(self, where, expected_type, received_type):
        if isinstance(where, ast.ASTNode):
            self._span = where.span
            where = where.span
        else:
            self._span = where
        self._value = "'{}': Wrong type of argument. Expected '{}' got '{}'"\
            .format(where.get_line(), expected_type, received_type)

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaComponentTooManyParams(BananaException):
    def __init__(self, span):
        self._span = span
        self._value = "Too many params provided to '{}' (line {})".format(
            span, span.get_lineno()
        )

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaComponentMixingParams(BananaException):
    def __init__(self, span, named_is_wrong):
        self._span = span
        if named_is_wrong:
            self._value = "'{}' should be named as " \
                          "previous parameters are.".format(span)
        else:
            self._value = "'{}' should not be named as " \
                          "previous parameters are.".format(span)

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaComponentIncorrectParamName(BananaException):
    def __init__(self, found, component):
        if isinstance(component, ast.ASTNode):
            component = component.span
        if isinstance(found, ast.ASTNode):
            self._span = found.span
            found = found.span
        else:
            self._span = found
        self._value = "Incorrect parameter name. Parameter '{}' " \
                      "does not exists on component {}."\
                      .format(found, component)

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaComponentAlreadyDefined(BananaException):
    def __init__(self, first_def, second_def):
        self._value = "Component already defined!\n" \
                      "  First definition:  '{}'\n" \
                      "  Second definition: '{}'"\
            .format(first_def, second_def)

    def __str__(self):
        return self._value

    def get_span(self):
        # TODO(Joan): This could be a real span instead of this one.
        return ast.DUMMY_SPAN


class BananaShadowingComponentError(BananaException):
    def __init__(self, where, comp):
        self._span = where
        self._value = "Shadowing component '{}'. " \
                      "Please use another variable name.".format(comp)

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaAssignmentError(BananaException):
    def __init__(self, lhs, rhs):
        self._value = "You can't assign '{}' to '{}'".format(lhs, rhs)

    def __str__(self):
        return self._value

    def get_span(self):
        return ast.DUMMY_SPAN


class BananaGrammarBug(BananaException, p.ParseFatalException):
    def __init__(self, error):
        super(BananaGrammarBug, self).__init__(pstr=error)
        self._value = "Bug found in the grammar!" \
                      " Please report this error: {}".format(error)

    def __str__(self):
        return self._value

    def get_span(self):
        return ast.DUMMY_SPAN


class BananaJsonObjShadowingError(BananaException, p.ParseFatalException):
    def __init__(self, span, error):
        self._span = span
        error = "Can't shadow property already defined in {}".format(error)
        super(BananaJsonObjShadowingError, self).__init__(pstr=error)

    def __str__(self):
        return self.msg

    def get_span(self):
        return self._span


class BananaTypeCheckerBug(BananaException):
    def __init__(self, error):
        self._value = "Bug found in the TypeChecker!" \
                      " Please report this error: {}".format(error)

    def __str__(self):
        return self._value

    def get_span(self):
        return ast.DUMMY_SPAN


class BananaEvalBug(BananaException):
    def __init__(self, error):
        self._value = "Bug found in the evaluator!" \
                      " Please report this error: {}".format(error)

    def __str__(self):
        return self._value

    def get_span(self):
        return ast.DUMMY_SPAN


class BananaUnknown(BananaException):
    def __init__(self, ident):
        self._span = ident.span
        self._value = "Unknown '{}'".format(
            ident.into_unmodified_str()
        )

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaUnknownOperator(BananaException):
    def __init__(self, span, operator, for_type):
        self._span = span
        self._value = "Unknown operator '{}' for type '{}'".format(
            operator,
            for_type
        )

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaPropertyDoesNotExists(BananaException):
    def __init__(self, dotpath, on_type=None):
        self._span = dotpath.span
        if on_type is None:
            self._value = "Error at '{}': Property '{}' " \
                          "does not exists"\
                .format(
                    dotpath.span.get_line(),
                    dotpath.into_unmodified_str()
                )
        else:
            self._value = "Error at '{}': Property '{}' " \
                          "does not exists on type '{}'"\
                .format(
                    dotpath.span.get_line(),
                    dotpath.into_unmodified_str(),
                    str(on_type)
                )

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaTypeError(BananaException):
    def __init__(self, expected_type, found_type=None, span=None):
        self._span = span
        if expected_type is None:
            class DummyType(object):
                def __str__(self):
                    return "_"
            expected_type = DummyType
        if found_type is None:
            if isinstance(expected_type, list):
                self._value = "Type error found. Expected" \
                              " one among '{}'"\
                    .format(', '.join(map(lambda x: str(x), expected_type)))
            else:
                self._value = "Type error found. Expected '{}'".format(
                    str(expected_type)
                )
        else:
            if isinstance(expected_type, list):
                self._value = "Type error found. Expected" \
                              " one among '{}', found '{}'"\
                    .format(', '.join(map(lambda x: str(x), expected_type)),
                            str(found_type))
            else:
                self._value = "Type error found. Expected" \
                              " '{}', found '{}'"\
                    .format(str(expected_type), str(found_type))

    def __str__(self):
        return self._value

    def get_span(self):
        if self._span is None:
            return ast.DUMMY_SPAN
        return self._span


class BananaAssignCompError(BananaException):
    def __init__(self, span):
        self._span = span
        self._value = "Component objects " \
                      "can't be assigned to " \
                      "properties of other objects"

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span


class BananaConnectionError(BananaException):

    def __init__(self, ident_from, ident_to, type_from, possible_connections):
        self._span = ident_to.span
        self._value = "Can't connect '{}' (line:{})" \
                      " to '{}' (line:{})," \
                      " '{}' can only be connected to {}"\
            .format(
                ident_from.val, ident_from.span.get_lineno(),
                ident_to.val, ident_to.span.get_lineno(),
                type_from, possible_connections)

    def __str__(self):
        return self._value

    def get_span(self):
        return self._span
