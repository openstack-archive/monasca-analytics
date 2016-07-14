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


def array_to_str(array, multiline=False, indent=None):
    """
    Convert the provided dictionary into a readable str, by calling
    str on both the keys and the values.
    :type array: list
    :param array: the dictionary to convert.
    :type multiline: bool
    :param multiline: If each key value pair should be on its own line.
    :type indent: int
    :param indent: Indentation if multiline is True.
    :rtype: str
    :return: Returns the converted dict.
    """
    if len(array) == 0:
        return "[]"

    multiline = multiline or indent is not None

    def dispatch(value):
        if isinstance(value, list):
            return array_to_str(value, multiline, indent)
        if isinstance(value, dict):
            return dict_to_str(value, multiline, indent)
        return str(value)

    res = "["
    if multiline:
        res += "\n"
    join_str = ","
    if multiline:
        join_str += "\n"
    else:
        join_str += " "
    if indent is not None:
        join_str = " " * indent + join_str
    res += join_str.join(map(dispatch, array))
    if multiline:
        res += "\n"
    res += "]"

    return res


def dict_to_str(dictionary, multiline=False, indent=None):
    """
    Convert the provided dictionary into a readable str, by calling
    str on both the keys and the values.
    :type dictionary: dict
    :param dictionary: the dictionary to convert.
    :type multiline: bool
    :param multiline: If each key value pair should be on its own line.
    :type indent: int
    :param indent: Indentation if multiline is True.
    :rtype: str
    :return: Returns the converted dict.
    """
    if len(dictionary) == 0:
        return "{}"
    res = "{"
    if multiline:
        res += "\n"
    multiline = multiline or indent is not None
    for k, v in sorted(dictionary.iteritems(), key=lambda ke: str(ke[0])):
        if indent is not None:
            res += " " * indent
        if isinstance(v, dict):
            res += "{}: {}, ".format(str(k),
                                     dict_to_str(v, multiline, indent))
        elif isinstance(v, list):
            res += "{}: {}, ".format(str(k),
                                     array_to_str(v, multiline, indent))
        else:
            res += "{}: {}, ".format(str(k), str(v))
        if multiline:
            res += '\n'
    res = res[0:-2]
    res += "}"
    return res


def stable_repr(obj):
    """
    Convert the provided dictionary into a 'repr' str, by calling
    repr on both the keys and the values.
    :type obj: dict | str | float
    :param obj: the dictionary to convert.
    :rtype: str
    :return: Returns the converted dict.
    """

    if isinstance(obj, list):
        return "[" + ", ".join(map(stable_repr, obj)) + "]"
    elif not isinstance(obj, dict):
        return repr(obj)

    if len(obj) == 0:
        return "{}"

    res = "{"

    for k, v in sorted(obj.iteritems(), key=lambda ke: str(ke[0])):
        res += "{}: {}, ".format(repr(k), stable_repr(v))

    res = res[0:-2]
    res += "}"
    return res
