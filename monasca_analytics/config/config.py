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
import sys

import monasca_analytics.config.connection as connection
import monasca_analytics.config.creation as creation
import monasca_analytics.config.validation as validation
import monasca_analytics.source.base as msource

logger = logging.getLogger(__name__)


def instantiate_components(_config):
    """Instantiate the components from the configuration.

    :type _config: dict
    :param _config: configuration of the module to instantiate
    :rtype: dict
    :returns: the list of components
    """
    try:
        validation.validate_config(_config)
        logger.debug("Creating components according to configuration...")
        components = creation.create_components(_config)
        logger.debug("Done creating components. Creating link data...")
        links = connection.connect_components(components, _config)
        logger.debug("Done connecting components. Validating links...")
        validation.validate_links(links)
        logger.debug("Done validating links. Successful instantiation")
        return links
    except Exception as ex:
        logger.error("Failed to instantiate components")
        logger.error("Reason : " + str(ex))
        sys.exit(-1)


def collect_sources(links):
    """Collect the sources from the links and return them in a list

    :type links: dict
    :returns: List of sources
    :rtype: list[msource.BaseSource]
    """
    sources = []
    for key in links.keys():
        if isinstance(key, msource.BaseSource):
            sources.append(key)
    return sources
