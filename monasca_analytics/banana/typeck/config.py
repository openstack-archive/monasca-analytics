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

import monasca_analytics.ingestor.base as ingestor
import monasca_analytics.ldp.base as ldp
import monasca_analytics.sink.base as sink
import monasca_analytics.sml.base as sml
import monasca_analytics.source.base as source
import monasca_analytics.voter.base as voter

import monasca_analytics.banana.grammar.ast as ast
import monasca_analytics.banana.typeck.connections as conn
import monasca_analytics.banana.typeck.type_table as typetbl
import monasca_analytics.banana.typeck.type_util as u
import monasca_analytics.exception.banana as exception
import monasca_analytics.exception.monanas as exception_monanas
import monasca_analytics.util.common_util as introspect


import six


def typeck(banana_file):
    """
    Type-check the provided BananaFile instance.
    If it type check, it returns the associated TypeTable.
    :type banana_file: ast.BananaFile
    :param banana_file: The file to typecheck.
    :rtype: typetbl.TypeTable
    :return: Returns the TypeTable for this BananaFile
    """
    type_table = typetbl.TypeTable()
    statement_index = 0
    for stmt in banana_file.statements:
        lhs, rhs = stmt
        type_computed = typeck_rhs(rhs, type_table)
        type_table.set_type(lhs, type_computed, statement_index)
        statement_index += 1
    conn.typeck_connections(banana_file.connections, type_table)
    return type_table


def typeck_rhs(ast_value, type_table):
    """
    Type-check the provided ast value. And returns its type.
    This function does not support assignment,
    :type ast_value: ast.ASTNode
    :param ast_value: The ast_value to type check.
    :type type_table: typetbl.TypeTable
    :param type_table: The type table. Used for type lookup.
    :rtype: u.Component | u.Object | u.Number | u.String
    :return: Returns the computed type.
    """
    if isinstance(ast_value, ast.Number):
        return u.Number()
    if isinstance(ast_value, ast.StringLit):
        return u.String()
    if isinstance(ast_value, ast.Ident):
        return type_table.get_type(ast_value)
    if isinstance(ast_value, ast.DotPath):
        return type_table.get_type(ast_value)
    if isinstance(ast_value, ast.Expr):
        return typeck_expr(ast_value, type_table)
    if isinstance(ast_value, ast.JsonObj):
        return typeck_jsonobj(ast_value, type_table)
    if isinstance(ast_value, ast.Component):
        return typeck_component(ast_value, type_table)
    raise Exception("Unhandled ast value type {}!!".format(ast_value))


def typeck_jsonobj(json_obj, type_table):
    """
    Type-check a json-like object. If it succeeds
    it return the appropriate type describing this
    json like object. Raise an exception otherwise.
    :type json_obj: ast.JsonObj
    :param json_obj: The JsonObj ast node.
    :type type_table: typetbl.TypeTable
    :param type_table: The type table.
    :rtype: u.Object
    :return: Returns an instance of util.Object describing
             the full type of this json object.
    """
    root_type = u.Object(strict_checking=False)

    for k, v in six.iteritems(json_obj.props):
        sub_type = u.create_object_tree(k, typeck_rhs(v, type_table))
        u.attach_to_root(root_type, sub_type, json_obj.span)

    return root_type


def typeck_expr(expr, type_table):
    """
    Type-check the given expression. If the typecheck
    pass, the resulting type will be used for the strategy
    to use when evaluating this expression.
    :type expr: ast.Expr
    :param expr: The expression to typecheck.
    :type type_table: typetbl.TypeTable
    :param type_table: Type of the table
    :rtype: u.Number | u.String
    :return: Returns the type of the expression if possible
    :raise: Raise an exception
    """
    # In the case where we are just wrapping around
    # only one expression, the logic below
    # needs to be skipped.
    if len(expr.expr_tree) == 1:
        return typeck_rhs(expr.expr_tree[0], type_table)

    _type = None
    must_be_number = False

    def check_type(old_type, new_type):
        if new_type == old_type:
            return old_type
        elif new_type == u.String():
            if must_be_number:
                raise exception.BananaTypeError(
                    expected_type=u.Number,
                    found_type=new_type
                )
            if old_type is None:
                return new_type
            elif u.can_to_str(old_type):
                return new_type
            else:
                raise exception.BananaTypeError(
                    expected_type=old_type,
                    found_type=new_type
                )
        elif new_type == u.Number():
            if old_type is None:
                return new_type
            elif old_type == u.String():
                return old_type
            elif not old_type == u.Number():
                raise exception.BananaTypeError(
                    expected_type=old_type,
                    found_type=new_type
                )
        else:
            raise exception.BananaTypeError(
                expected_type=old_type,
                found_type=new_type
            )

    def allowed_symbol(current_type):
        if current_type == u.String():
            return ['+']
        else:
            return ['+', '-', '*', '/']

    for el in expr.expr_tree:
        if isinstance(el, ast.StringLit):
            _type = check_type(_type, u.String())
        elif isinstance(el, ast.Number):
            _type = check_type(_type, u.Number())
        elif isinstance(el, ast.Ident):
            ident_type = type_table.get_type(el)
            _type = check_type(_type, ident_type)
        elif isinstance(el, ast.DotPath):
            dotpath_type = type_table.get_type(el)
            _type = check_type(_type, dotpath_type)
        elif isinstance(el, ast.Expr):
            _type = check_type(_type, typeck_expr(el, type_table))
        elif isinstance(el, six.string_types):
            if el not in allowed_symbol(_type):
                raise exception.BananaUnknownOperator(expr.span, el, _type)
            if el in ['-', '*', '/']:
                must_be_number = True
        else:
            raise exception.BananaTypeError(
                expected_type=[u.Number.__name__, u.String.__name__,
                               u.Object.__name__],
            )

    # The final type if we made until here!
    return _type


def typeck_component(component, type_table):
    """
    Type-check the provided component. Returns
    the appropriate subclass of util.Component if
    successful, or raise an exception if there's
    an error.
    :type component: ast.Component
    :param component: The component ast node.
    :type type_table: typetbl.TypeTable
    :param type_table: the type table.
    :rtype: u.Source | u.Sink | u.Voter | u.Ldp | u.Sml | u.Ingestor
    :return: Returns the appropriate type for the component.
    """
    # TODO(Joan): This wont't work for type that are defined
    # TODO(Joan): at the language level. We need a registration service
    # TODO(Joan): to manage the Types of component that we can create
    # TODO(Joan): instead of this hacky function call.
    try:
        component_type = introspect.get_class_by_name(component.type_name.val)
        comp_params = component_type.get_params()
    except exception_monanas.MonanasNoSuchClassError:
        raise exception.BananaUnknown(
            component
        )

    # Compute the type of the component
    if issubclass(component_type, source.BaseSource):
        comp_type = u.Source(component_type.__name__, comp_params)
    elif issubclass(component_type, sink.BaseSink):
        comp_type = u.Sink(component_type.__name__, comp_params)
    elif issubclass(component_type, sml.BaseSML):
        comp_type = u.Sml(component_type.__name__, comp_params)
    elif issubclass(component_type, voter.BaseVoter):
        comp_type = u.Voter(component_type.__name__, comp_params)
    elif issubclass(component_type, ldp.BaseLDP):
        comp_type = u.Ldp(component_type.__name__, comp_params)
    elif issubclass(component_type, ingestor.BaseIngestor):
        comp_type = u.Ingestor(component_type.__name__, comp_params)
    else:
        raise exception.BananaTypeCheckerBug("Couldn't find a type for '{}'"
                                             .format(component.type_name.val))

    # Type check the parameters
    if len(component.args) > len(comp_params):
        raise exception.BananaComponentTooManyParams(component.span)

    # Does saying that parameter should either all have a name
    # or non at all satisfying? -> Yes
    # Are parameter all named?
    all_named = -1
    for arg in component.args:
        if arg.arg_name is not None:
            if all_named == 0:
                raise exception.BananaComponentMixingParams(arg.span, False)
            all_named = 1
        else:
            if all_named == 1:
                raise exception.BananaComponentMixingParams(arg.span, True)
            all_named = 0

    if all_named == 1:
        for arg in component.args:
            param = list(filter(lambda x:
                                x.param_name == arg.arg_name.inner_val(),
                                comp_params))
            if len(param) != 1:
                raise exception.BananaComponentIncorrectParamName(
                    component=component.type_name,
                    found=arg.arg_name
                )
            param = param[0]
            expr_type = typeck_rhs(arg.value, type_table)
            if not u.can_be_cast_to(expr_type, param.param_type):
                raise exception.BananaArgumentTypeError(
                    where=arg,
                    expected_type=param.param_type,
                    received_type=expr_type
                )
    else:
        for arg, param in zip(component.args, comp_params):
            arg.arg_name = ast.Ident(arg.span, param.param_name)
            expr_type = typeck_rhs(arg.value, type_table)
            if not u.can_be_cast_to(expr_type, param.param_type):
                raise exception.BananaArgumentTypeError(
                    where=arg,
                    expected_type=param.param_type,
                    received_type=expr_type
                )

    return comp_type
