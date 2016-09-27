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

import monasca_analytics.banana.deadpathck.dag as dag
import monasca_analytics.banana.emitter as emit
import monasca_analytics.banana.grammar.ast as ast
import monasca_analytics.banana.typeck.type_util as type_util
import monasca_analytics.exception.banana as exception


def deadpathck(banana_file, type_table, emitter=emit.PrintEmitter()):
    """
    Perform dead path elimination on the provided AST.
    This allow to remove branches and components that
    are not connected to a Sink.
    :type banana_file: ast.BananaFile
    :param banana_file: The AST tree we will clean.
    :type type_table monasca_analytics.banana.typeck.type_table.TypeTable
    :param type_table: The TypeTable of the provided AST.
    :type emitter: emit.Emitter
    :param emitter: Emitter for reporting warnings.
    """
    # Check that first argument is a banana file. Mainly
    # an excuse to remove the F401 warning.
    if not isinstance(banana_file, ast.BananaFile):
        raise Exception("Expected BananaFile as first argument.")

    # Look first for all branch that are "dead"
    connections = banana_file.connections  # type: ast.Connection

    # If there are no connections everything is considered
    # as dead.
    if connections is None:
        class EmptyConnections(object):
            connections = []
        connections = EmptyConnections()

    # Collect the nodes and connect them.
    dag_nodes = {}
    # Create all the nodes
    for ident in banana_file.components.keys():
        dag_nodes[ident] = dag.DagNode(type_table.get_type(ident))
    # Connect them
    for ident_from, ident_to in connections.connections:
        dag_from = dag_nodes[ident_from]
        dag_to = dag_nodes[ident_to]
        dag_from.children.append(dag_to)
        dag_to.parents.append(dag_from)

    # Start from every sources and for each, check if the path is dead
    for node in dag_nodes.values():
        if isinstance(node.typec, type_util.Source):
            node.visit()

    # We can now remove all the components that are "dead"
    # from the list of connections
    for ident, node in dag_nodes.iteritems():
        if not node.is_alive():
            emitter.emit_warning(
                ident.span,
                "Dead code found, this component is not in a path "
                "starting from a 'Source' and ending with a 'Sink'."
            )
            banana_file.components.pop(ident)
            connections.connections = filter(
                lambda edge: edge[0] != ident and edge[1] != ident,
                connections.connections
            )

    # TODO(Joan): We could also remove them from the statements.
    # TODO(Joan): But for this we need a dependency graph between
    # TODO(Joan): statements to make sure we don't break the code.


def contains_at_least_one_path_to_a_sink(banana_file, type_table):
    """
    Check that there's at least one path to a sink in the list
    of components.
    To run this pass, you need to make sure you
    have eliminated all dead path first.

    :type banana_file: ast.BananaFile
    :param banana_file: The AST to check.
    :type type_table monasca_analytics.banana.typeck.type_table.TypeTable
    :param type_table: The TypeTable of the provided AST.
    :raise: Raise an exception if there's no Sink.
    """
    def is_sink(comp):
        type_comp = type_table.get_type(comp)
        return isinstance(type_comp, type_util.Sink)

    def is_src(comp):
        type_comp = type_table.get_type(comp)
        return isinstance(type_comp, type_util.Source)

    comp_vars = banana_file.components.keys()
    at_least_one_sink = len(filter(is_sink, comp_vars)) > 0
    at_least_one_source = len(filter(is_src, comp_vars)) > 0

    if not at_least_one_sink:
        raise exception.BananaNoFullPath("Sink")
    if not at_least_one_source:
        raise exception.BananaNoFullPath("Source")
