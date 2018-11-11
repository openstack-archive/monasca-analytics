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

"""
Util files to manipulates banana types.

The list of possible types is as follow:

    * `Number`
    * `Boolean`
    * `String`
    * `Object` (Json-like object)
    * `Component.Source.<class-name>`
    * `Component.Ingestor.<class-name>`
    * `Component.Sink.<class-name>`
    * `Component.Voter.<class-name>`
    * `Component.Ldp.<class-name>`
    * `Component.Sml.<class-name>`

where <class-name> will be the component class name defined
in the code base.

For type defined in banana such as Json parsers, <class-name>
refers the name they are defined with.
"""
import abc
import six

import monasca_analytics.banana.grammar.ast as ast
import monasca_analytics.exception.banana as exception
import monasca_analytics.util.string_util as strut


@six.add_metaclass(abc.ABCMeta)
class IsType(object):
    """
    Any class that represents a Banana type should inherit
    from this class.
    """

    def __ne__(self, other):
        # Dispatch to eq function
        return not self.__eq__(other)

    @abc.abstractmethod
    def default_value(self):
        pass

    @abc.abstractmethod
    def to_json(self):
        pass


class Any(IsType):
    """
    Any type. This type should be used by component's writer when
    they have a complex handling of parameters. This is not
    recommended though as it move the error handling to
    the component writer.
    """

    def __str__(self):
        return "TypeAny"

    def __eq__(self, _):
        # Any type is equal to nothing not even itself.
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getitem__(self, _):
        return Any()

    def __hash__(self):
        raise Exception("Any type should not be used in dictionaries.")

    def default_value(self):
        return {}

    def to_json(self):
        return {"id": "any"}


class String(IsType):
    """
    String Type.
    """

    def __str__(self):
        return "TypeString"

    def __eq__(self, other):
        return isinstance(other, String)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))

    def default_value(self):
        return ""

    def to_json(self):
        return {"id": "string"}


class Number(String):
    """
    Number type. Banana has only floating point value.
    """

    def __str__(self):
        return "TypeNumber"

    def __eq__(self, other):
        return isinstance(other, Number)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))

    def default_value(self):
        return 0

    def to_json(self):
        return {"id": "number"}


class Enum(String):
    """
    Enum type. This type is a way to constraint a string or number,
    to a specific set of values.
    """

    def __init__(self, variants):
        self.variants = variants

    def __eq__(self, other):
        return isinstance(other, Enum) and self.variants == other.variants

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.variants)

    def __str__(self):
        return "TypeEnum < {} >".format(','.join(self.variants))

    def default_value(self):
        return ""

    def to_json(self):
        return {
            "id": "enum",
            "variants": self.variants
        }


def attach_to_root(root_obj, obj1, span, erase_existing=False):
    """
    Attach the object obj1 to the root_obj object type.

    :type root_obj: Object
    :param root_obj: The root object
    :type obj1: Object
    :param obj1: The object to attach.
    :type span: Span
    :param span: The span for this change.
    :type erase_existing: bool
    :param erase_existing: Set to true if the root type should
                           always be erased.
    """
    for key, child_type in six.iteritems(obj1.props):
        if key in root_obj.props:
            root_sub_type = root_obj.props[key]
            # Both are object -> recurse
            if isinstance(root_sub_type, Object) and\
               isinstance(child_type, Object):
                attach_to_root(root_sub_type, child_type, span, erase_existing)
            elif erase_existing:
                root_obj.props[key] = child_type
            else:
                raise exception.BananaTypeError(
                    expected_type=root_sub_type,
                    found_type=child_type,
                    span=span
                )
        else:
            # We can simply attach the new type!
            root_obj.props[key] = child_type


def create_object_tree(dot_path, value):
    """
    Create a linear tree of object type from the dot_path.
    Also work when dot_path is an Ident or StringLit.

    :type dot_path: ast.DotPath | ast.Ident | ast.StringLit
    :param dot_path: The ast node that forms a linear tree of type.
    :type value: Object | String | Number
    :param value: the value to set at the end of the linear tree.
    :rtype: Object
    :return: Returns the created object
    """
    if is_comp(value):
        raise exception.BananaAssignCompError(dot_path.span)

    # {a.b.c: value}
    root_object = Object(strict_checking=False)
    if isinstance(dot_path, ast.DotPath):
        # {a: value}
        if len(dot_path.properties) == 0:
            root_object.props[dot_path.varname.inner_val()] = value
        else:
            # {a: <Object>}
            root_object.props[dot_path.varname.inner_val()] = \
                Object(strict_checking=False)
            # {b.c: value}
            current_obj = root_object.props[dot_path.varname.inner_val()]
            last_index = len(dot_path.properties) - 1
            for index, sub_prop in enumerate(dot_path.properties):
                sub_prop_name = sub_prop.inner_val()
                if index != last_index:
                    current_obj.props[sub_prop_name] = \
                        Object(strict_checking=False)
                    current_obj = current_obj.props[sub_prop_name]
                else:
                    current_obj.props[sub_prop_name] = value
    else:
        # Ident and StringLit are captured here.
        root_object.props[dot_path.inner_val()] = value
    return root_object


class Object(String):
    """
    Object Type. The value that are dictionary-like have this type.
    """

    def __init__(self, props=None, strict_checking=True):
        if props is None:
            props = {}
        self.props = props
        # Strict checking is off for all objects defined within the banana
        # language. It is on by default for components so that they can
        # force the type checker to throw errors when we try to access
        # or to modify unknown properties
        self.strict_checking = strict_checking

    def __getitem__(self, key):
        # a.b or a."b"
        if isinstance(key, ast.Ident) or isinstance(key, ast.StringLit):
            if key.inner_val() not in self.props:
                raise exception.BananaPropertyDoesNotExists(key,
                                                            on_type=self)
            return self.props[key.inner_val()]

        # a.b.c
        if isinstance(key, ast.DotPath):
            if key.varname.inner_val() not in self.props:
                raise exception.BananaPropertyDoesNotExists(key.varname,
                                                            on_type=self)
            sub_object = self.props[key.varname.inner_val()]
            if len(key.properties) == 0:
                return sub_object
            # Recurse
            if isinstance(sub_object, Object):
                return sub_object[key.next_dot_path()]
            if isinstance(sub_object, Any):
                return sub_object

            raise exception.BananaPropertyDoesNotExists(key.next_dot_path(),
                                                        on_type=sub_object)

        raise exception.BananaTypeCheckerBug(
            "Unreachable code in Object.__getitem__ reached."
        )

    def __str__(self):
        if self.strict_checking:
            return "TypeStruct < {} >".format(strut.dict_to_str(self.props))
        else:
            return "TypeObject < {} >".format(strut.dict_to_str(self.props))

    def __eq__(self, other):
        return self.props == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.props)

    def default_value(self):
        default_value = {}
        for key, val in six.iteritems(self.props):
            default_value[key] = val.default_value()
        return default_value

    def to_json(self):
        res = {"id": "object", "props": {}}
        for key, val in six.iteritems(self.props):
            res["props"][key] = val.to_json()
        return res


class Component(IsType):
    """
    Type of all components. While not strictly used directly, it
    is very useful to performs checks on variable that are supposed
    to be any of the available components.
    """

    def __init__(self, ctor_properties=None, class_name=None):
        """
        Component type

        :type ctor_properties:
                list[monasca_analytics.component.params.ParamDescriptor]
        :param ctor_properties:
        :type class_name: str
        :param class_name: Name of the class if there's any.
        """
        self.ctor_properties = ctor_properties
        self.class_name = class_name

    def __str__(self):
        if self.class_name is None:
            return "TypeComponent"
        else:
            return self.class_name + "(" +\
                ",".join(map(lambda x: x.param_name + "=" + str(x.param_type),
                             self.ctor_properties))\
                + ")"

    def __setitem__(self, dot_path, value):
        """
        Attempt to set the value at 'dot_path' to 'value'.

        :type dot_path: ast.DotPath
        :param dot_path: The path of the property
        :type value: String | Enum | Object | Number
        :param value: The new type to set.
        """
        if self.ctor_properties is None:
            raise exception.BananaTypeCheckerBug(
                "Component type can't have properties"
            )

        if len(dot_path.properties) == 0:
            for arg in self.ctor_properties:
                if arg.param_name == dot_path.varname.inner_val():
                    if not can_be_cast_to(value, arg.param_type):
                        raise exception.BananaArgumentTypeError(
                            expected_type=arg.param_type,
                            received_type=value,
                            where=dot_path.span
                        )
                    else:
                        return
        else:
            for arg in self.ctor_properties:
                if arg.param_name == dot_path.varname.inner_val():
                    if isinstance(arg.param_type, Any):
                        return
                    elif isinstance(arg.param_type, Object):
                        next_dot_path = dot_path.next_dot_path()
                        sub_arg_type = arg.param_type[next_dot_path]
                        if not can_be_cast_to(value, sub_arg_type):
                            raise exception.BananaArgumentTypeError(
                                expected_type=sub_arg_type,
                                received_type=value,
                                where=next_dot_path.span
                            )
                        else:
                            return
                    else:
                        raise exception.BananaPropertyDoesNotExists(
                            dot_path.next_dot_path(),
                            arg.param_type
                        )

        raise exception.BananaPropertyDoesNotExists(dot_path, on_type=self)

    def __getitem__(self, dot_path):
        """
        Return the type of the given item.

        :type dot_path: ast.DotPath
        :param dot_path: The path to follow
        :return:
        """
        if self.ctor_properties is None:
            raise exception.BananaTypeCheckerBug(
                "Component type can't have properties"
            )

        if len(dot_path.properties) == 0:
            for arg in self.ctor_properties:
                if arg.param_name == dot_path.varname.inner_val():
                    return arg.param_type
        else:
            for arg in self.ctor_properties:
                if arg.param_name == dot_path.varname.inner_val():
                    if isinstance(arg.param_type, Object):
                        return arg.param_type[dot_path.next_dot_path()]
                    else:
                        raise exception.BananaPropertyDoesNotExists(
                            dot_path.next_dot_path(),
                            arg.param_type
                        )

        raise exception.BananaPropertyDoesNotExists(dot_path, on_type=self)

    def __eq__(self, other):
        return isinstance(other, Component)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))

    def default_value(self):
        return None

    def to_json(self):
        res = {"id": "component", "name": self.class_name, "args": []}
        for arg in self.ctor_properties:
            res["args"].append(arg.to_json())
        return res


class Source(Component):
    """
    Source type. All component that inherits from BaseSource have
    this type in Banana.
    """
    def __init__(self, class_name, ctor_properties):
        super(Source, self).__init__(ctor_properties, class_name)

    def __eq__(self, other):
        return self.class_name == other.class_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.class_name)


class Ingestor(Component):
    """
    Ingestor type. All component that inherits from BaseIngestor have
    this type in Banana.
    """
    def __init__(self, class_name, ctor_properties):
        super(Ingestor, self).__init__(ctor_properties, class_name)

    def __eq__(self, other):
        return self.class_name == other.class_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.class_name)


class Sink(Component):
    """
    Sink type. All component that inherits from BaseSink have
    this type in Banana.
    """
    def __init__(self, class_name, ctor_properties):
        super(Sink, self).__init__(ctor_properties, class_name)

    def __eq__(self, other):
        return self.class_name == other.class_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.class_name)


class Voter(Component):
    """
    Voter type. All component that inherits from BaseVoter have
    this type in Banana.
    """
    def __init__(self, class_name, ctor_properties):
        super(Voter, self).__init__(ctor_properties, class_name)

    def __eq__(self, other):
        return self.class_name == other.class_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.class_name)


class Ldp(Component):
    """
    Ldp type. All component that inherits from BaseLdp have
    this type in Banana.
    """
    def __init__(self, class_name, ctor_properties):
        super(Ldp, self).__init__(ctor_properties, class_name)

    def __eq__(self, other):
        return self.class_name == other.class_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.class_name)


class Sml(Component):
    """
    Sml type. All component that inherits from BaseSml have
    this type in Banana.
    """
    def __init__(self, class_name, ctor_properties):
        super(Sml, self).__init__(ctor_properties, class_name)

    def __eq__(self, other):
        return self.class_name == other.class_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.class_name)


def get_type(ast_node):
    """
    Returns the type for the given ast node.
    This function only works for literal node such as
    Number, StringLit and JsonObj.
    :type ast_node: ast.Number | ast.StringLit | ast.JsonObj | ast.Component
    :param ast_node: the node.
    :return: Returns the appropriate type.
    """
    if isinstance(ast_node, ast.Number):
        return Number()
    if isinstance(ast_node, ast.StringLit):
        return String()
    if isinstance(ast_node, ast.JsonObj):
        return Object(strict_checking=False)
    if isinstance(ast_node, ast.Component):
        return Component()
    return None


def can_to_str(_type):
    """
    Check if we the type can be cast to str.
    :param _type: Type to check
    :return: Returns True if it can be casted
    """
    return isinstance(_type, String)


def is_comp(_type):
    """
    :type _type: String | Number | Object | Component
    :param _type: Type to check.
    :rtype: bool
    :return: Returns True if the provided _type is a component
    """
    return isinstance(_type, Component)


def can_be_cast_to(_type1, _type2):
    """
    Check if the given type `_type1` can be cast into `_type2`.
    :type _type1: String | Number | Enum | Object
    :param _type1: Type to try to change into _type2
    :type _type2: String | Number | Enum | Object
    :param _type2: Type reference.
    :return: Returns true if the conversion can be done.
    """
    if isinstance(_type2, Any):
        return True
    elif _type1 == _type2:
        return True
    elif _type2 == String():
        return can_to_str(_type1)
    elif isinstance(_type2, Enum):
        return isinstance(_type1, String) or isinstance(_type2, Enum)
    elif isinstance(_type1, Object) and isinstance(_type2, Object):
        if not _type2.strict_checking:
            return True
        else:
            for prop_name, prop_type in six.iteritems(_type2.props):
                if prop_name not in _type1.props:
                    return False
                if not can_be_cast_to(_type1.props[prop_name], prop_type):
                    return False
            return True
    return False
