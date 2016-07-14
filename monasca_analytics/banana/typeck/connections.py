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

import monasca_analytics.banana.typeck.type_util as util
import monasca_analytics.exception.banana as exception

valid_connections_types = {
    util.Source: [util.Ingestor, util.Ldp],
    util.Ingestor: [util.Sml, util.Sink],
    util.Sml: [util.Voter, util.Sink],
    util.Voter: [util.Ldp, util.Sink],
    util.Ldp: [util.Sink],
    util.Sink: []
}


def typeck_connections(connection, type_table):
    """
    Once all variable have been type-checked, we can
    try to type-check connections.
    :type connection: monasca_analytics.banana.grammar.ast.Connection
    :param connection: The connection to type-check
    :type type_table: monasca_analytics.banana.typeck.type_table.TypeTable
    :param type_table: The table with all variable already type-checked.
    :raise Raise an exception if there's a type error in connections.
    """
    if connection is not None:
        for ident_from, ident_to in connection.connections:
            type_from = type_table.get_type(ident_from)
            type_to = type_table.get_type(ident_to)
            if not util.is_comp(type_from):
                raise exception.BananaTypeError(
                    expected_type=util.Component(),
                    found_type=type_from
                )
            if not util.is_comp(type_to):
                raise exception.BananaTypeError(
                    expected_type=util.Component(),
                    found_type=type_to
                )
            if type(type_to) not in valid_connections_types[type(type_from)]:
                possible_types = map(lambda x: x.__name__,
                                     valid_connections_types[type(type_from)])
                raise exception.BananaConnectionError(
                    ident_from, ident_to, type_from, possible_types
                )
