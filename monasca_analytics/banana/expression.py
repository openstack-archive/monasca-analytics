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
import types

import monasca_analytics.banana.bytecode.assembler as asbl
import monasca_analytics.banana.private as priv
import monasca_analytics.exception.banana as exception
import pyparsing as p


logger = logging.getLogger(__name__)


class ExpressionParser(object):

    def __init__(self):
        """
        Create a parser that parse arithmetic expressions. They can
        contains variable identifiers or raw numbers. The meaning
        for the identifiers is left to the
        """
        number = p.Regex(r'\d+(\.\d*)?([eE]\d+)?')
        identifier = p.Word(p.alphas)
        terminal = identifier | number
        self._expr = p.infixNotation(terminal, [
            (p.oneOf('* /'), 2, p.opAssoc.LEFT),
            (p.oneOf('+ -'), 2, p.opAssoc.LEFT)
        ])

    def parse(self, string, code=asbl.Code()):
        """
        Parse a given string and construct an Evaluator
        :type string: basestring
        :param string: String to parse.
        :type code: ass.Code
        :param code: Generated code will be written here.
        :return: Returns an evaluator that will returns a value
                 given the appropriate environment to resolve
                 variables.
        """
        tree = self._expr.parseString(string)[0]
        self._build_tree(tree, code)

    def parse_tree(self, expr):
        """
        Parse the given string and return the generated tree
        by pyparsing.
        :type expr: str
        :param expr: Expression to parse.
        :return: Returns the generated tree.
        """
        return self._expr.parseString(expr)

    @staticmethod
    def _build_tree(subtree, code):
        """
        :type subtree: list
        :param subtree: Sub tree to parse
        :type code: ass.Code
        :param code: Generated code is written here.
        """
        operator = filter(priv.is_op, subtree)[0]
        pushed_one_stack_value = False
        for child in filter(priv.is_not_op, subtree):
            if isinstance(child, basestring):
                code(asbl.Local(child))
                if not pushed_one_stack_value:
                    pushed_one_stack_value = True
                else:
                    ExpressionParser._push_op(operator, code)
            else:
                ExpressionParser._build_tree(child, code)
                if not pushed_one_stack_value:
                    pushed_one_stack_value = True
                else:
                    ExpressionParser._push_op(operator, code)

    @staticmethod
    def _push_op(operator, code):
        if operator == '+':
            code.BINARY_ADD()
        elif operator == '-':
            code.BINARY_SUBTRACT()
        elif operator == '/':
            code.BINARY_DIVIDE()
        elif operator == '*':
            code.BINARY_MULTIPLY()


def create_fn_with_config(env, expr_string):
    """
    Create an evaluator given the expected
    environment renaming and expression.
    :type env: dict[str, str]
    :param env: Environment to use.
    :type expr_string: str
    :param expr_string: String containing the expression
                        to be evaluated
    :returns: Returns a function that accept one argument
              expected to be the environment.
    """
    code = asbl.Code()
    # Argument
    code(asbl.Local('__monanas__env'))
    code.co_argcount = 1
    # Create local variables
    for key, value in env.iteritems():
        code(asbl.Call(
            asbl.Getattr(
                asbl.Local('__monanas__env'), 'get'),
            [asbl.Const(value)]),
            asbl.LocalAssign(str(key)))
    parser = ExpressionParser()
    try:
        parser.parse(expr_string, code)
    except p.ParseException as e:
        raise exception.BananaInvalidExpression(e.message)
    code.RETURN_VALUE()
    final_fn = types.FunctionType(code.code(), globals())
    return final_fn


def validate_environment(env):
    """
    Validate the given arguments that create_fn_with_config
    is expecting.
    :param env: Environment spec
    """
    for key, val in env.iteritems():
        if not isinstance(key, basestring):
            raise exception.BananaEnvironmentError(
                "{} is not a valid key (only string are)".format(key)
            )
        if not isinstance(val, basestring):
            raise exception.BananaEnvironmentError(
                "{} is not a valid value (only string are)".format(val)
            )


def validate_expression(expr_string):
    """
    Validate the provided expression string.
    :type expr_string: str
    :param expr_string: Expression string to validate.
    :returns: Returns a handle that can be use to validate
              name usage against an environment.
    :raises: exception.BananaInvalidExpression
    """
    if not isinstance(expr_string, basestring):
        raise exception.BananaArgumentTypeError(
            expected_type=basestring,
            received_type=type(expr_string)
        )
    parser = ExpressionParser()
    try:
        res = parser.parse_tree(expr_string)
        return ExpressionHandle(res, expr_string)
    except p.ParseException as e:
        raise exception.BananaInvalidExpression(e.message)


def validate_name_binding(expr_handle, environment):
    """
    Validate the name binding in the expr_handle for
    the provided environment.
    :type expr_handle: ExpressionHandle
    :param expr_handle: The expression handle
    :type environment: dict
    :param environment: The environment
    """
    if not isinstance(expr_handle, ExpressionHandle):
        raise exception.BananaArgumentTypeError(
            expected_type=ExpressionHandle,
            received_type=type(expr_handle)
        )

    def collect_names(subtree):
        """
        Collect names used in this subtree
        :type subtree: list
        :param subtree: subtree
        """
        for child in subtree:
            if isinstance(child, basestring):
                if priv.is_not_op(child):
                    names.add(child)
            else:
                collect_names(child)
    names = set()
    collect_names(expr_handle.tree)
    for name_binding in environment.keys():
        if name_binding not in names:
            raise exception.BananaInvalidExpression(
                "This expression ('{}') can't be used with the provided "
                "environment: '{}'.\nReason: '{}' is not defined.".format(
                    expr_handle.original_str,
                    environment,
                    name_binding
                )
            )


class ExpressionHandle(object):
    def __init__(self, tree, original_string):
        self.tree = tree
        self.original_str = original_string
