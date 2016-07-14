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

import monasca_analytics.banana.grammar.ast as ast
import monasca_analytics.exception.banana as exception


class EvaluationContext(object):
    """Evalutation context for an AST evaluation"""

    def __init__(self):
        """
        Construct an evaluation context using the type table
        as based for the variable needed to be created.
        """
        self._variables = {}
        self._components = {}

    def set_variable(self, name, value):
        """Set the variable value."""
        if isinstance(value, tuple) and len(value) == 2:
            comp_type, config = value
            comp_name = name.varname.inner_val()
            self._components[comp_name] = comp_type(
                comp_name,
                config
            )
            self._variables[comp_name] = config
        elif not set_property(self._variables, name, value):
            raise exception.BananaEvalBug(
                "set_variable can only be used with DotPath or Ident."
            )

    def get_components(self):
        return self._components

    def get_variable(self, name):
        """Returns the variable value."""
        return self._variables[name]

    def get_prop_of_variable(self, name, prop):
        """Returns the sub property of the given variable name."""
        variable = self._variables[name]
        for el in prop:
            variable = variable[el]
        return variable


def set_property(root_object, name, value):
    """
    Set the property name of the root_object to value.
    :type root_object: dict
    :param root_object: The root object
    :type name: ast.DotPath | ast.Ident | ast.StringLit
    :param name: Name of
    :param value:
    :return: Returns true if succeeded.
    """
    if isinstance(name, ast.Ident) or isinstance(name, ast.StringLit):
        root_object[name.inner_val()] = value
        return True
    elif isinstance(name, ast.DotPath):
        _create_as_many_object_as_needed(root_object, name, value)
        return True
    return False


def _create_as_many_object_as_needed(root_object, dot_path, value):
    """
    Create as many object as needed to be able to access the
    nested property.

    :type root_object: dict
    :param root_object: The root object
    :type dot_path: ast.DotPath
    :param dot_path: Dot Path to use.
    :type value: object
    :param value: Any value to set.
    """
    name = dot_path.varname.inner_val()

    if len(dot_path.properties) == 0:
        root_object[name] = value
        return

    if name in root_object:
        variable = root_object[name]
    else:
        variable = {}

    current_var = variable
    last_index = len(dot_path.properties) - 1

    for index, subpath in enumerate(dot_path.properties):
        subpath_name = subpath.inner_val()
        if index != last_index:
            if subpath_name in current_var:
                current_var = current_var[subpath_name]
            else:
                new_object = {}
                current_var[subpath_name] = new_object
                current_var = new_object
        else:
            current_var[subpath_name] = value

    root_object[name] = variable
