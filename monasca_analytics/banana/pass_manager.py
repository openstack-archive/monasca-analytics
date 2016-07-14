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

import pyparsing as p

import monasca_analytics.banana.deadpathck.config as deadpathck
import monasca_analytics.banana.emitter as emit
import monasca_analytics.banana.eval.config as ev
import monasca_analytics.banana.eval.ctx as ctx
import monasca_analytics.banana.grammar.base_ast as span_util
import monasca_analytics.banana.grammar.config as grammar
import monasca_analytics.banana.typeck.config as typeck
import monasca_analytics.exception.banana as exception


def execute_banana_string(banana_str, driver, emitter=emit.PrintEmitter()):
    """
    Execute the provided banana string.
    It will run the parse phase, and the typechecker.
    :type banana_str: str
    :param banana_str: The string to parse and type check.
    :type driver: monasca_analytics.spark.driver.DriverExecutor
    :param driver: Driver that will manage the created
        components and connect them together.
    :type emitter: emit.Emitter
    :param emitter: Emitter for reporting errors/warning.
    """
    try:
        # Convert the grammar into an AST
        parser = grammar.banana_grammar(emitter)
        ast = parser.parse(banana_str)
        # Compute the type table for the given AST
        type_table = typeck.typeck(ast)
        # Remove from the tree path that are "dead"
        deadpathck.deadpathck(ast, type_table, emitter)
        # Check that there's at least one path to be executed
        deadpathck.contains_at_least_one_path_to_a_sink(ast, type_table)
        # Evaluate the script
        ev.eval_ast(ast, type_table, driver)
    except exception.BananaException as err:
        emitter.emit_error(err.get_span(), str(err))
    except p.ParseSyntaxException as err:
        emitter.emit_error(span_util.from_parse_fatal(err), err.msg)
    except p.ParseFatalException as err:
        emitter.emit_error(span_util.from_parse_fatal(err), err.msg)


def compute_type_table(banana_str):
    """
    Compute the type table for the provided banana string
    if possible.
    :type banana_str: str
    :param banana_str: The string to parse and type check.
    """
    # Convert the grammar into an AST
    parser = grammar.banana_grammar()
    ast = parser.parse(banana_str)
    # Compute the type table for the given AST
    return typeck.typeck(ast)


def compute_evaluation_context(banana_str, cb=lambda *a, **k: None):
    """
    Compute the evaluation context for the provided
    banana string.
    :type banana_str: str
    :param banana_str: The string to parse and type check.
    :param cb: Callback called after each statement
    """
    parser = grammar.banana_grammar()
    ast = parser.parse(banana_str)
    type_table = typeck.typeck(ast)
    context = ctx.EvaluationContext()

    def custom_cb(_type, lhs, value):
        cb(context, _type, lhs, value)

    ev.eval_statements_generic(ast.statements, type_table, context, custom_cb)
