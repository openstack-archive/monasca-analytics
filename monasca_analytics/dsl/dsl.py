#!/usr/bin/env python

# Copyright (c) 2016 Hewlett Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not used this file except in compliance with the License. You may obtain
# a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy
import json
import logging
import os

import schema

from monasca_analytics.config import const
from monasca_analytics.config import validation
from monasca_analytics.exception import dsl as err
import monasca_analytics.util.common_util as cu


logger = logging.getLogger(__name__)

MODULE = "module"


class MonanasDSL(object):

    def __init__(self, config_file_path=None):
        """Constructor with an optional configuration file path

        If the configuration file is provided, it will be loaded at
        MonanasDLS creation time.
        If no configuration file path is provided, the default base
        configuration defined in config.const will be used.

        :type config_file_path: str
        :param config_file_path: path to the file containing the configuration
                                 that will be loaded at MonansDSL creation
        """
        if config_file_path:
            self.load_configuration(config_file_path)
        else:
            self._config = const.get_default_base_config()
            self._init_ids_dictionary()

    def add_component(self, _component_config):
        """Add the component configuration passed as parameter

        Add it to MonanasDSL configuration, and return a new unique ID
        generated for it.
        The configuration passed as parameter is validated, raising exceptions
        if the module does not exist or the configuration is invalid.

        :type _component_config: dict
        :param _component_config: configuration of the component to be added
        :rtype: str
        :returns: Component ID for the added component
        :raises: MonanasNoSuchClassError -- if the defined class doesn't
                 exist or is not of a valid type
        :raises: SchemaError -- if the configuration is not valid for
                 the class.
        """
        if type(_component_config) == str:
            _component_config = json.loads(_component_config)
        clz = cu.get_class_by_name(_component_config[MODULE])
        clz.validate_config(_component_config)
        comp_type = cu.get_component_type(_component_config[MODULE])
        comp_id = self._generate_id(comp_type)
        self._config[comp_type][comp_id] = _component_config
        self._config[const.CONNECTIONS][comp_id] = []
        return comp_id

    def modify_component(self, comp_id, params_path, value):
        """Overrides the value of the configuration path of a component

        Modifies the configuration of the component defined by comp_id,
        following the path in the dictionary defined by params_path, and
        assigning the value value.

        :type comp_id: str
        :param comp_id: ID of the component to be modified
        :type params_path: list
        :param params_path: parameters path to modify in the config
        :type value: str | int | float
        :param value: new value to be assigned, will be parsed
                      according to the expected configuration
        :rtype: bool
        :returns: True if the component was modified (or if the modification
                  result was the same as the existing configuration),
                  False otherwise
        :raises: SchemaError -- if the new configuration would not be valid
        """
        comp_type = self._get_type_by_id(comp_id)
        if not comp_type:
            return False
        new_conf = copy.deepcopy(self._config[comp_type][comp_id])
        logger.debug("Modifying " + comp_id + ", existing config = " +
                     str(new_conf))
        clz = cu.get_class_by_name(new_conf[MODULE])
        for var_type in [str, int, float]:
            try:
                parsed_value = var_type(value)
            except ValueError as e:
                logger.debug(str(e))
                continue
            new_conf = self._modify_dictionary(new_conf, params_path,
                                               parsed_value)
            try:
                clz.validate_config(new_conf)
                logger.debug("New validated config = " + str(new_conf))
                self._config[comp_type][comp_id] = new_conf
                return True
            except schema.SchemaError as e:
                logger.debug(str(e))
                continue
        return False

    def remove_component(self, component_id):
        """Remove a component from the configuration.

        Removes from the configuration the component whose ID matches the
        one passed as parameter.

        :type component_id: str
        :param: component_id: ID of the component to be removed
        :rtype: bool
        :returns: True if the component was removed, False otherwise
        :raises: DSLExistingConnection -- if at least a connection exists with
                 the component as origin or destination.
        """
        if self._is_connected(component_id):
            raise err.DSLExistingConnection("Cannot remove component " +
                                            component_id +
                                            " because it is still connected")
        for comp_type in const.components_types:
            if component_id in self._config[comp_type].keys():
                del self._config[comp_type][component_id]
                del self._config[const.CONNECTIONS][component_id]
                return True
        return False

    def connect_components(self, origin_id, dest_id):
        """Connect the two components passed as parameter.

        Being the origin the first one and the destination the second one.
        If the connection already existed, False is returned. If we created a
        new connection, True is returned.
        If any of the components is not defined, a DSLInexistentComponent
        exception is raised.

        :type origin_id: str
        :param origin_id: ID of the component at the origin of the connection
        :type dest_id: str
        :param dest_id: ID of the component at the destination of the
                        connection
        :rtype: bool
        :returns: True if the components were connected, False if
                  the connection already existed
        :raises: DSLInexistentComponent -- if either the origin or the
                 destination are not defined in the configuration
        """
        if not self._component_defined(origin_id):
            raise err.DSLInexistentComponent(origin_id)
        if not self._component_defined(dest_id):
            raise err.DSLInexistentComponent(dest_id)
        if dest_id in self._config[const.CONNECTIONS][origin_id]:
            return False
        if not self._validate_connection_by_ids(origin_id, dest_id):
            raise err.DSLInvalidConnection("Connection from " + origin_id +
                                           " to " + dest_id +
                                           " is not allowed")
        self._config[const.CONNECTIONS][origin_id].append(dest_id)
        return True

    def disconnect_components(self, origin_id, dest_id):
        """Disconnect the component dest_id from origin_id

        If the connection from origin_id to dest_id exists, it is removed,
        and the function returns true.
        If it didn't exist, the function returns false and nothing happens

        :type origin_id: str
        :param origin_id: ID of the component at the origin of the connection
        :type dest_id: str
        :param dest_id: ID of the component at the destination of the
                        connection
        :rtype: bool
        :returns: True if the components were already disconnected,
                  False if the connection didn't exist in the first place
        """
        if origin_id in self._config[const.CONNECTIONS]:
            if dest_id in self._config[const.CONNECTIONS][origin_id]:
                self._config[const.CONNECTIONS][origin_id].remove(dest_id)
                return True
        return False

    def load_configuration(self, config_file_path):
        """Load a configuration from the file passed as parameter

        :type config_file_path: str
        :param config_file_path: file path containing the
               configuration that will be loaded
        """
        self._config = cu.parse_json_file(config_file_path)
        self._init_ids_dictionary()

    def _init_ids_dictionary(self):
        self.ids_by_type = {
            const.SOURCES: ("src", 0),
            const.INGESTORS: ("ing", 0),
            const.SMLS: ("sml", 0),
            const.VOTERS: ("vot", 0),
            const.SINKS: ("snk", 0),
            const.LDPS: ("ldp", 0),
            const.CONNECTIONS: ("connections", 0)}

    def save_configuration(self, config_file_path, overwrite_file=True):
        """Save the configuration to the file passed as parameter

        :type config_file_path: str
        :param config_file_path: file path where the configuration
                                 will be saved
        :type overwrite_file: bool
        :param overwrite_file: True will overwrite the file if it exists,
                               False will make the function return without
                               saving.
        :rtype: bool
        :returns: True if the configuration was saved,
                  False otherwise
        """
        if os.path.exists(config_file_path) and\
                os.stat(config_file_path).st_size > 0 and\
                overwrite_file is False:
            return False
        with open(config_file_path, "w") as f:
            str_config = json.dumps(self._config)
            f.write(str_config)
        return True

    def _generate_id(self, comp_type):
        """Generate a new ID for the component type passed as parameter

        After the ID is generated, the last max checked number is stored
        in the ids_by_type dictionary

        :type comp_type: str
        :param comp_type: type of component for which the ID will
                          be created
        :raises: KeyError -- if the comp_type does not correspond to a
                             component type of the configuration
        """
        typ, num = self.ids_by_type[comp_type]
        num += 1
        while(typ + str(num) in self._config[comp_type].keys()):
            num += 1
        self.ids_by_type[comp_type] = (typ, num)
        return typ + str(num)

    def _get_type_by_id(self, component_id):
        """Gets the type of a copmonent from its ID

        :type component_id: str
        :param component_id: ID of a component
        :rtype: str
        :returns: type of component for the ID passed as parameter
        """
        for comp_type in const.components_types:
            if component_id in self._config[comp_type]:
                return comp_type

    def _component_defined(self, component_id):
        """Check if a component is defined in the configuration

        :type component_id: str
        :param component_id: ID of a component
        :rtype: bool
        :returns: True if the component is defined in the configuration
        """
        comp_type = self._get_type_by_id(component_id)
        if not comp_type:
            return False
        return True

    def _is_connected(self, component_id):
        """Check if a component is connected

        Both in and out connections will be considered: if there is any
        connection with component_id as either source or destination, this
        function will return true. Empty connections lists are ignored.

        :type component_id: str
        :param component_id: ID of a component
        :rtype: bool
        :returns: True if the component is connected to another component
                  according to the configuration, False otherwise
        """
        for origin_id, dest_ids in self._config[const.CONNECTIONS].iteritems():
            if dest_ids == []:
                continue
            if origin_id == component_id:
                return True
            for dest_id in dest_ids:
                if dest_id == component_id:
                    return True
        return False

    def _validate_connection_by_ids(self, origin_id, dest_id):
        """Validate the connection from origin_id to dest_id

        The connection from the component with ID = origin_id
        to the component with ID = dest_id is validated according to the
        valid connections dictionary defined in the validation module.

        :type origin_id: str
        :param origin_id: ID of the origin component
        :type dest_id: str
        :param dest_id: ID of the destination component
        :rtype: bool
        :returns: True if the connection is allowed, False otherwise
        """
        origin_type = self._get_type_by_id(origin_id)
        dest_type = self._get_type_by_id(dest_id)
        if dest_type in validation.valid_connection_types[origin_type]:
            return True
        return False

    def _modify_dictionary(self, target_dict, params_path, value):
        """Override the value at the end of a path in the target_dictionary

        Modify the dictionary passed as first parameter, assigning the value
        passed as last parameter to the key path defined by params_path

        :type target_dict: dict
        :param target_dict: target to be modified
        :type params_path: list[str]
        :param params_path: hierarchy of keys to navigate in
                            the dictionary, pointing the leave to modify
        :type value: object
        :param value: Value that will be assigned to the path defined
                      by params_path in the dictionary
        :rtype dict
        :returns: Modified dictionary
        """
        aux = target_dict
        for i, param in enumerate(params_path):
            if param not in aux.keys():
                aux[param] = {}
            if i == len(params_path) - 1:
                aux[param] = value
            else:
                aux = aux[param]
        return target_dict
