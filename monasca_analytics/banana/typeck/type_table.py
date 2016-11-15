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

import monasca_analytics.banana.grammar.ast as ast
import monasca_analytics.banana.typeck.type_util as util
import monasca_analytics.exception.banana as exception
import monasca_analytics.util.string_util as strut


class TypeTable(object):
    """
    Type table. Support lookup for JsonLike object.
    Json-like object have properties that needs to be
    type-checked. The TypeTable allows to store
    that information as well. All type values are
    rooted by their variable name.

    Every-time a variable type is erased, we create a new
    snapshot of the variables types. This allow to have
    variable where the type change as the statement are
    being executed.
    """
    def __init__(self):
        self._variables_snapshots = [(0, {})]
        self._variables = self._variables_snapshots[0][1]

    def get_type(self, var, statement_index=None):
        variables = self.get_variables(statement_index)
        if isinstance(var, ast.Ident):
            if var in variables:
                return variables[var]
            else:
                raise exception.BananaUnknown(var)
        # If we encounter a dot path:
        if isinstance(var, ast.DotPath):
            if var.varname in variables:
                if len(var.properties) > 0:
                    return variables[var.varname][var.next_dot_path()]
                else:
                    return variables[var.varname]
            else:
                raise exception.BananaUnknown(var.varname)
        raise exception.BananaTypeCheckerBug("Unkown type for {}".format(var))

    def set_type(self, var, _type, statement_index):
        """
        Set the type for the given var to _type.

        :type var: ast.Ident | ast.DotPath
        :param var: The var to set a type.
        :type _type: util.Object | util.Component | util.String | util.Number
        :param _type: The type for the var.
        :type statement_index: int
        :param statement_index: The statement at which this assignment was
                                made.
        """
        if _type is None:
            raise exception.BananaTypeCheckerBug(
                "'None' is not a valid banana type"
            )

        if isinstance(var, ast.Ident):
            self._check_needs_for_snapshot(var, _type, statement_index)
            self._variables[var] = _type
            return

        if isinstance(var, ast.DotPath):
            if util.is_comp(_type) and len(var.properties) > 0:
                raise exception.BananaAssignCompError(var.span)

            if len(var.properties) == 0:
                self._check_needs_for_snapshot(
                    var.varname,
                    _type,
                    statement_index
                )
                self._variables[var.varname] = _type
            else:
                if var.varname in self._variables:
                    var_type = self._variables[var.varname]
                    if isinstance(var_type, util.Object):
                        new_type = util.create_object_tree(
                            var.next_dot_path(), _type)
                        util.attach_to_root(var_type, new_type, var.span,
                                            erase_existing=True)
                    elif isinstance(var_type, util.Component):
                        var_type[var.next_dot_path()] = _type
                    else:
                        raise exception.BananaTypeError(
                            expected_type=util.Object,
                            found_type=type(var)
                        )
                # Var undeclared, declare its own type
                else:
                    new_type = util.create_object_tree(var.next_dot_path(),
                                                       _type)
                    self._variables[var.varname] = new_type
            return
        raise exception.BananaTypeCheckerBug("Unreachable code reached.")

    def get_variables(self, statement_index=None):
        """
        Returns the list of variables with their associated type.

        :type statement_index: int
        :param: Statement index.
        :rtype: dict[str, util.Object|util.Component|util.String|util.Number]
        """
        if statement_index is None:
            return self._variables

        variables = {}
        for created_at, snap in self._variables_snapshots:
            if created_at < statement_index:
                variables = snap
            else:
                break

        return variables

    def get_variables_snapshots(self):
        return self._variables_snapshots

    def _check_needs_for_snapshot(self, var, _type, statement_index):
        if var in self._variables:
            # If we shadow a component, we need to raise an error
            if util.is_comp(self._variables[var]):
                raise exception.BananaShadowingComponentError(
                    where=var.span,
                    comp=self._variables[var].class_name
                )

            # If we change the type of the variable, we create a new snapshot:
            # This is very strict but will allow to know exactly how
            # the type of a variable (or a property) changed.
            if self._variables[var] != _type:
                self._create_snapshot(statement_index)

    def _create_snapshot(self, statement_index):
        """
        Create a new snapshot of the variables.
        :type statement_index: int
        :param statement_index: index of the statement
            (should be strictly positive)
        """
        new_snapshot = copy.deepcopy(self._variables)
        self._variables_snapshots.append((
            statement_index, new_snapshot
        ))
        self._variables = new_snapshot

    def to_json(self):
        """
        Convert this type table into a dictionary.
        Useful to serialize the type table.

        :rtype: dict
        :return: Returns this type table as a dict.
        """
        res = {}
        for key, val in self._variables.iteritems():
            res[key.inner_val()] = val.to_json()
        return res

    def __contains__(self, key):
        """
        Test if the type table contains or not the provided
        path. This function is more permissive than the other two.
        It will never raise any exception (or should aim not to).
        :type key: basestring | ast.Ident | ast.DothPath
        :param key: The key to test.
        :return: Returns True if the TypeTable contains a type for the
                 given path or identifier.
        """
        if isinstance(key, basestring):
            return key in self._variables

        if isinstance(key, ast.Ident):
            return key.val in self._variables

        if isinstance(key, ast.DotPath):
            res = key.varname in self._variables
            if not res:
                return False
            val = self._variables[key.varname]
            for prop in key.properties:
                if isinstance(val, util.Object):
                    if prop in val.props:
                        val = val[prop]
                else:
                    return False
            return True

        return False

    def __str__(self):
        return strut.dict_to_str(self._variables)
