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
import operator

import monasca_analytics.banana.eval.ctx as ctx
import monasca_analytics.banana.eval.old_style as into
import monasca_analytics.banana.grammar.ast as ast
import monasca_analytics.banana.typeck.type_util as type_util
import monasca_analytics.config.connection as connection
import monasca_analytics.config.const as conf_const
import monasca_analytics.exception.banana as exception
import monasca_analytics.util.common_util as introspect

import six


logger = logging.getLogger(__name__)


def eval_ast(ast_root, type_table, driver):
    """
    Evaluate the provided AST by instantiating
    the appropriate components and connecting them
    together using the Driver interface.
    :type ast_root: ast.BananaFile
    :param ast_root: AST to evaluate.
    :type type_table: monasca_analytics.banana.typeck.type_table.TypeTable
    :param type_table: the TypeTable (used to create configurations)
    :type driver: monasca_analytics.spark.driver.DriverExecutor
    :param driver: Driver that will manage the created
        components and connect them together.
    """
    logger.debug("Creating the config dictionary from the AST...")
    _config = conf_const.get_default_base_config()

    try:
        logger.debug("Creating components according to banana config...")
        components = eval_create_components(ast_root.statements, type_table)
        convert_connections(ast_root.connections, _config)
        logger.debug("Done creating components. Creating link data...")
        # Pre-process to convert to old style components
        components_old_style = into.into_old_conf_dict(components)
        links = connection.connect_components(components_old_style, _config)
        logger.debug("Done connecting components. Successful instantiation")
    except Exception as ex:
        logger.error("Failed to instantiate components")
        logger.error("Reason : " + str(ex))
        return

    # Restart Spark using the new config
    logger.debug("Stop pipeline")
    driver.stop_pipeline()
    logger.debug("Set new links")
    driver.set_links(links)
    logger.debug("Start pipeline")
    driver.start_pipeline()


def convert_connections(connections, output_config):
    """
    Augment the output_config object with the list of
    connections
    :type connections: ast.Connection
    :param connections: The list of connections.
    :type output_config: dict
    :param output_config: Config where the links will be written.
    """
    output_config[conf_const.CONNECTIONS] = connections.connections_cache


def eval_create_components(statements, type_table):
    """
    Convert the provided AST into the old dict configuration.
    :type statements: list[(ast.ASTNode, ast.ASTNode)]
    :param statements: The AST to process
    :type type_table: monasca_analytics.banana.typeck.type_table.TypeTable
    :param type_table: the type table.
    :rtype: dict[str, Component]
    :return: Returns the component keyed by name.
    """
    context = ctx.EvaluationContext()

    eval_statements_generic(
        statements,
        type_table,
        context
    )
    return context.get_components()


def eval_statements_generic(
        statements,
        type_table,
        context,
        cb=lambda *a, **k: None):
    """
    Eval the list of statements, and call the cb after evaluating
    each statement providing it with the type of the value, the
    left hand side ast node, and the computed value.
    :type statements: list[(ast.ASTNode, ast.ASTNode)]
    :param statements: The AST to process
    :type type_table: monasca_analytics.banana.typeck.type_table.TypeTable
    :param type_table: the type table.
    :type context: ctx.EvaluationContext
    :param context: evaluation context that will collect
        all intermediary results.
    :type cb: (type_util.IsType, ast.ASTNode, object) -> None
    :param cb: Callback called after each statement evaluation.
    """
    stmt_index = 0
    for stmt in statements:
        lhs, rhs = stmt
        expected_type = type_table.get_type(lhs, stmt_index + 1)
        stmt_index += 1
        # Provide the expected type
        value = eval_rhs(context, rhs, expected_type)
        # Call the cb with the expected_type of the value
        # The lhs node and the value
        cb(expected_type, lhs, value)
        # Store result if referenced later.
        context.set_variable(lhs, value)


def eval_rhs(context, ast_node, expected_type):
    """
    Eval the right hand side node.
    :type context: ctx.EvaluationContext
    :param context: Evaluation context.
    :type ast_node: ast.ASTNode
    :param ast_node: the node to evaluate.
    :type expected_type: type_util.IsType
    :param expected_type: The expected type of this computation.
    :return: Returns the result of this evaluation.
    """
    if isinstance(ast_node, ast.StringLit):
        return ast_node.inner_val()
    if isinstance(ast_node, ast.Ident):
        return context.get_variable(ast_node.inner_val())
    if isinstance(ast_node, ast.JsonObj):
        return eval_object(context, ast_node, expected_type)
    if isinstance(ast_node, ast.Number):
        return ast_node.val
    if isinstance(ast_node, ast.DotPath):
        variable_name = ast_node.varname.inner_val()
        prop = map(lambda x: x.inner_val(), ast_node.properties)
        return context.get_prop_of_variable(variable_name, prop)
    if isinstance(ast_node, ast.Expr):
        return eval_expr(context, ast_node, expected_type)
    if isinstance(ast_node, ast.Component):
        return eval_comp(context, ast_node, expected_type)
    raise Exception("Unhandled ast value type {}!!".format(ast_node))


def eval_comp(context, comp, expected_type):
    """
    Instantiate the given component, computing
    the required config.
    :type context: ctx.EvaluationContext
    :param context: Evaluation context.
    :type comp: ast.Component
    :param comp: the node to evaluate.
    :type expected_type: type_util.IsType
    :param expected_type: The expected type of this computation.
    :return: Returns the instantiated component.
    """
    arguments = {}
    # Compute arguments
    for arg in comp.args:
        arg_name = ast.DotPath(arg.arg_name.span, arg.arg_name, [])
        arg_value = eval_rhs(context, arg.value, expected_type[arg_name])
        arguments[arg.arg_name.inner_val()] = arg_value
    # Lookup component
    component_type = introspect.get_class_by_name(comp.type_name.val)
    # Get default config for the component
    conf = component_type.get_default_config()
    # Update modified params
    for k, val in six.iteritems(arguments):
        conf[k] = val
    # Delay evaluation until we do the assign
    return component_type, conf


def eval_object(context, obj, expected_type):
    """
    Evaluate the provided object
    :type context: ctx.EvaluationContext
    :param context: Evaluation context.
    :type obj: ast.JsonObj
    :param obj: The expression to evaluate
    :type expected_type: type_util.IsType
    :param expected_type: The expected type of this computation.
    :return: Returns the computed value
    """
    result = expected_type.default_value()
    for name, val in six.iteritems(obj.props):
        subtype = expected_type[name]
        ctx.set_property(result, name, eval_rhs(context, val, subtype))
    return result


def eval_expr(context, expr, expected_type):
    """
    Eval the provided expression
    :type context: ctx.EvaluationContext
    :param context: Evaluation context.
    :type expr: ast.Expr
    :param expr: The expression to evaluate
    :type expected_type: type_util.IsType
    :param expected_type: The expected type of this computation.
    :rtype: str | float
    :return: Returns the computed value
    """
    if len(expr.expr_tree) == 1:
        return eval_rhs(context, expr.expr_tree[0], expected_type)

    if isinstance(expected_type, type_util.Number):
        result = 0
        cast_func = float
    elif isinstance(expected_type, type_util.String):
        result = ""
        cast_func = str
    else:
        raise exception.BananaEvalBug(
            "Expected type for an expression can only be "
            "'TypeNumber' or 'TypeString', got '{}'".format(
                str(expected_type))
        )
    current_operator = operator.add
    for el in expr.expr_tree:
        if isinstance(el, six.string_types) and el in ['+', '-', '*', '/']:
            current_operator = get_op_func(el)
        else:
            value = eval_rhs(context, el, expected_type)
            value = cast_func(value)
            result = current_operator(result, value)
    return result


def get_op_func(op_str):
    if op_str == '+':
        return operator.add
    if op_str == '-':
        return operator.sub
    if op_str == '*':
        return operator.mul
    if op_str == '/':
        return operator.div
    raise exception.BananaEvalBug(
        "Unknown operator '{}'".format(op_str)
    )
