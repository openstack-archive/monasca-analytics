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

import copy
import json
import logging

from monasca_analytics.config import const as config_const
from monasca_analytics.dsl import const as dsl_const
from monasca_analytics.dsl import dsl
from monasca_analytics.dsl import parser
from monasca_analytics.exception import dsl as err
import monasca_analytics.util.common_util as cu

logger = logging.getLogger(__name__)


class DSLInterpreter(object):

    def __init__(self):
        self.file_in_use = None
        self.dsl = dsl.MonanasDSL()
        self.mappings = {}

    def execute_string(self, str_program):
        """Parse and execute the command/s in the string passed as parameter

        :type str_program: str
        :param str_program: command to be executed
        :rtype: str
        :returns: execution result
        """
        info = parser.get_parser().parseString(str_program)
        return self.execute(info)

    def execute_file(self, file_program):
        """Parse and execute the command/s in the file passed as parameter

        :type file_program: str
        :param file_program: path to the file containing the
                             command to be executed
        :rtype: str
        :returns: execution result
        """
        info = parser.get_parser().parseFile(file_program)
        return self.execute(info)

    def execute(self, info):
        """Execute parsed command/s

        :type info: dict
        :param info: containing the parsed instructions
        :rtype: str
        :returns: execution result
        """
        for cmd in info:
            for key in cmd.keys():
                if key == dsl_const.CREATE:
                    return self.create(cmd[key][0], cmd[key][1])
                elif key == dsl_const.CONNECT:
                    return self.connect(cmd[key][0], cmd[key][1])
                elif key == dsl_const.DISCONNECT:
                    return self.disconnect(cmd[key][0], cmd[key][1])
                elif key == dsl_const.LOAD:
                    return self.load(cmd[key][0])
                elif key == dsl_const.SAVE_AS:
                    return self.save(cmd[key][0])
                elif key == dsl_const.SAVE:
                    return self.save()
                elif key == dsl_const.REMOVE:
                    return self.remove(cmd[key][0])
                elif key == dsl_const.MODIFY:
                    return self.modify(
                        cmd[key][0], cmd[key][1:-1], cmd[key][-1])
                elif key == dsl_const.PRINT:
                    if len(cmd[key]) > 0:
                        return self.prnt(cmd[key][0])
                    else:
                        return self.prnt_all()
                elif key == dsl_const.LIST:
                    if len(cmd[key]) > 0:
                        return self.list(cmd[key][0])
                    else:
                        return self.list_all()
                elif key == dsl_const.HELP:
                    return self.help()
                else:
                    return logger.warn("Wrong command" + str(cmd))

    def create(self, varname, modulename):
        """Add a module defined by modulename in the configuration

        :type varname: str
        :param varname: name of the variable representing
                        the new component
        :rtype: str
        :returns: new component ID
        """
        clz = cu.get_class_by_name(modulename)
        conf = copy.deepcopy(clz.get_default_config())
        comp_id = self.dsl.add_component(conf)
        self.mappings[varname] = comp_id
        return comp_id

    def connect(self, origin_varname, dest_varname):
        """Connect two components

        :type origin_varname: str
        :param origin_varname: variable name or ID of the source
                               component of the connection
        :type dest_varname: str
        :param dest_varname: variable name or ID of the destination
                            component of the connection
        :rtype: bool
        :returns: True if the connection was performed,
                  False otherwise
        """
        origin_id = self._get_id(origin_varname)
        dest_id = self._get_id(dest_varname)
        return self.dsl.connect_components(origin_id, dest_id)

    def _get_id(self, name_or_id):
        """Get the ID from a name or ID

        :type name_or_id: str
        :param name_or_id: variable name or ID
        :rtype: str
        :returns: ID
        """
        if name_or_id in self.mappings.keys():
            return self.mappings[name_or_id]
        for comp_type in config_const.components_types:
            if name_or_id in self.dsl._config[comp_type]:
                return name_or_id
        raise err.DSLInterpreterException("undefined variable: " + name_or_id)

    def disconnect(self, origin_varname, dest_varname):
        """Disconnect two components

        :type origin_varname: str
        :param origin_varname: variable name or ID of the source
                               component of the connection
        :type dest_varname: str
        :param dest_varname: variable name or ID of the destination
                             component of the connection
        :rtype: bool
        :returns: True if the components were disconnected,
                  False otherwise
        """
        origin_id = self._get_id(origin_varname)
        dest_id = self._get_id(dest_varname)
        return self.dsl.disconnect_components(origin_id, dest_id)

    def load(self, filepath):
        """Load configuration from a file

        :type filepath: str
        :param filepath: path to the file to be loaded
        """
        self.dsl.load_configuration(filepath)
        self.file_in_use = filepath

    def save(self, filepath=None):
        """Save configuration to a file

        :type filepath: str
        :param filepath: (Optional) path to the file where the configuration
                         will be saved. If the path is not provided, the last
                         file used for saving or loading will be used.
        """
        if not filepath:
            filepath = self.file_in_use
        saved = self.dsl.save_configuration(filepath, overwrite_file=True)
        if saved:
            self.file_in_use = filepath
        return saved

    def remove(self, varname):
        """Remove a variable or ID from the configuration

        :type varname: str
        :param varname: variable name or ID mapped to the component
                        that will be removed from the configuration
        """
        remove_id = self._get_id(varname)
        return self.dsl.remove_component(remove_id)

    def modify(self, varname, params, value):
        """Override the value of the configuration path of a component

        :type varname: str
        :param varname: variable name or ID mapped to the component
        :type params: list
        :param params: path to be modified in the configuration
        :type value: float | int | str
        :param value: value to assign
        """
        modify_id = self._get_id(varname)
        return self.dsl.modify_component(modify_id, params, value)

    def prnt(self, varname):
        """Print the configuration of the module/s defined by varname

        If varname is a variable or ID associated to a particular component,
        the configuration of that component will be printed. If if is a type
        of components, the configurations of all components of that type
        will be printed.

        :type varname: str
        :param varname: variable, ID or type to be printed
        :rtype: str
        :returns: requested configuration in string format
        """
        if varname in self.dsl._config.keys():
            return self._json_print(self.dsl._config[varname])
        itemId = self._get_id(varname)
        for k in config_const.components_types:
            if itemId in self.dsl._config[k]:
                return self._json_print(self.dsl._config[k][itemId])

    def prnt_all(self):
        """Print the the whole configuration

        :rtype: str
        :returns: whole configuration in string format
        """
        return self._json_print(self.dsl._config)

    def _json_print(self, jstr):
        """Format Json as a clean string"""
        return json.dumps(jstr, indent=4, separators=(',', ': '))

    def list(self, key):
        """List the available components of the type passed as parameter"""
        ret = ""
        if key in config_const.components_types:
            for name in cu.get_available_class_names(key):
                ret += "- " + name + "\n"
        return ret

    def list_all(self):
        """List all available components grouped by type"""
        ret = ""
        for key in config_const.components_types:
            ret += "- " + key + "\n"
            for name in cu.get_available_class_names(key):
                ret += "    - " + name + "\n"
        return ret

    def help(self):
        return """
Available commands
    - print: prints current configuration
    - list: shows available modules
    - load: loads a config from a file
    - save: saves a config to a file
    - <var> = <module>: instantiates module <module>, referenced by <var>
    - <var1>-><var2>: connects the module <var1> to the module <var2>
    - <var1>!-><var2>: disconnects the module <var1> from the module <var2>
    - rm <var>: removes the module corresponding to <var>
    - exit: finishes the execution of monanas command line
"""
