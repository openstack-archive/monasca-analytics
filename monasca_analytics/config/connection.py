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

import monasca_analytics.config.const as const
import monasca_analytics.exception.monanas as err


logger = logging.getLogger(__name__)


def connect_components(components, _config):
    """Connects the components using the information from the configuration

    :type components: dict
    :param components: components to connect
    :type _config: dict
    :param _config: configuration containing the
                    connections definitions
    :rtype: dict
    :returns: Dictionary where keys are IDs of sources of connections,
              and values are their destinations IDs.
    """
    return _perform_all_connections(const.CONNECTIONS, _config, components)


def _perform_all_connections(connection_kind, _config, components):
    """Connect all component that are of the given kind.

    :type connection_kind: str
    :param connection_kind: Kind of connection (feedback or flow)
    :type _config: dict
    :param _config: configuration containing the connections
    :type components: dict
    :param components: components to connect.
    :rtype: dict
    :returns: Dictionay where keys are IDs of sources of connections,
              and values are their destinations IDs.
    """
    links = {}
    for origin_id in _config[connection_kind].keys():
        for comp_type in const.components_types:
            if origin_id in components[comp_type]:
                component = components[comp_type][origin_id]
                connections_list = _config[connection_kind][origin_id]
                _perform_connections(
                    component, connections_list,
                    components, links)
    return links


def _perform_connections(origin, connections_list, components, links):
    """Connect 'origin' with all destinations in connections_list

    :type origin: str
    :param origin: origin component
    :type connections_list: list[str]
    :param connections_list: destinations IDs to be connected
    :type components: dict
    :param components: all components
    :type links: dict
    :param links: links that we are going to represent
    """
    if origin not in links:
        links[origin] = []

    if not connections_list:
        logger.debug("No connections for {}".format(origin))
        return

    for dest_id in connections_list:
        if dest_id in components[const.INGESTORS].keys():
            ingestor = components[const.INGESTORS][dest_id]
            links[origin].append(ingestor)
            continue
        if dest_id in components[const.SMLS].keys():
            sml = components[const.SMLS][dest_id]
            links[origin].append(sml)
            continue
        if dest_id in components[const.VOTERS].keys():
            voter = components[const.VOTERS][dest_id]
            links[origin].append(voter)
            continue
        if dest_id in components[const.SINKS].keys():
            sink = components[const.SINKS][dest_id]
            links[origin].append(sink)
            continue
        if dest_id in components[const.LDPS].keys():
            ldp = components[const.LDPS][dest_id]
            links[origin].append(ldp)
            continue
        raise err.MonanasWrongConnectoinError(
            "wrong component defined in connection : " + dest_id)
