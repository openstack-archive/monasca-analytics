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


import monasca_analytics.banana.emitter as emit
import monasca_analytics.banana.grammar.base_ast as base
import monasca_analytics.exception.banana as exception
import monasca_analytics.util.string_util as strut
import pyparsing as p


ASTNode = base.ASTNode
Span = base.Span


class BananaFile(object):

    def __init__(self, emitter=emit.PrintEmitter()):
        self.imports = []
        self._emitter = emitter
        # Components is a dict where keys
        # are the name of the var and
        # values are of type Component
        self.components = dict()
        # Statement are component
        # creation or variable creation
        self.statements = []
        self.connections = None

    def add_component_ctor(self, dot_path, component):
        """
        Add a component if the component
        does not already exists. If it does exists,
        then this raises an Error.
        :type dot_path: DotPath
        :param dot_path: Name of the variable or property path
        :type component: Component
        :param component: AST part that will contains all properties
        """
        if not isinstance(dot_path, DotPath):
            raise exception.BananaAssignmentError(
                dot_path.span, component.span)
        if not len(dot_path.properties) == 0:
            raise exception.BananaAssignmentError(
                dot_path.span, component.span)
        if dot_path.varname in self.components:
            other_dot_path = filter(
                lambda x: x == dot_path,
                self.components.keys())[0]
            no_effect_str = dot_path.span.str_from_to(component.span)
            collision_str = other_dot_path.span.str_from_to(
                self.components[other_dot_path].span)
            self._emitter.emit_warning(
                dot_path.span,
                "Statement has no effect: '{}'".format(no_effect_str)
            )
            self._emitter.emit_warning(
                other_dot_path.span,
                "It collides with: '{}'".format(collision_str)
            )
        else:
            self.components[dot_path.varname] = component
            self.statements.append((dot_path, component))

    def add_assignment(self, dot_path, ast_value):
        """
        Add an assignment to a property or a variable.
        We don't check at this point whether or not the variable
        has collision with a component.
        This will be done during the name resolution pass.
        :type dot_path: DotPath
        :param dot_path: Name of the variable or property
        :type ast_value: Ident | JsonObj | StringLit | Number | DotPath
        :param ast_value: Ast node this variable is assigned to.
        """
        if not isinstance(dot_path, DotPath):
            raise exception.BananaAssignmentError(
                dot_path.span,
                ast_value.span
            )
        self.statements.append((dot_path, ast_value))

    def add_connections(self, connections):
        """
        Add a new set of connections between components
        This function performs the same checks as the one
        performs when components are connected. It warns
        on redundant connections.
        :type connections: Connection
        :param connections: AST node that contains the collected connections.
        """
        if self.connections is None:
            self.connections = connections
        else:
            self.connections.merge_and_reset_inputs_outputs(
                connections,
                self._emitter
            )

    def statements_to_str(self):
        return "{ " + ', '.join(
            map(lambda x: '{} = {}'.format(x[0], x[1]), self.statements)
        ) + ' }'

    def __str__(self):
        res = "BananaFile { "
        res += 'components: { '
        res += strut.dict_to_str(self.components)
        res += ' }, '
        res += 'statements: ' + self.statements_to_str()
        res += 'connections: { '
        res += str(self.connections)
        res += " } }"
        return res


def make_span(s, l, t):

    def compute_hi(init_loc, tokens):
        hi = init_loc
        for tok in tokens:
            if isinstance(tok, ASTNode):
                hi = max(hi, tok.span.hi)
            elif isinstance(tok, basestring):
                hi += len(tok)
            elif isinstance(tok, p.ParseResults):
                hi = max(hi, compute_hi(init_loc, tok))
            else:
                raise exception.BananaGrammarBug(
                    "Couldn't create span for: {}".format(tok)
                )
        return hi

    if len(t) > 0:
        span_hi = compute_hi(l, t)
        return Span(s, l, span_hi)
    else:
        return Span(s, l, 2)


class Number(ASTNode):
    def __init__(self, span, val):
        """
        Construct a Number ast node.
        :type span: Span
        :param span: Span for this number
        :type val: str
        :param val: Value for this number
        """
        super(Number, self).__init__(span)
        self.val = float(val)

    def __str__(self):
        return "Number< {} >".format(self.val)

    def into_unmodified_str(self):
        return str(self.val)


class StringLit(ASTNode):
    def __init__(self, span, val):
        """
        Construct a StringLit ast node.
        :type span: Span
        :param span: Span for this string
        :type val: str
        :param val: Value for this string
        """
        super(StringLit, self).__init__(span)
        self.val = val

    def __hash__(self):
        return hash(self.inner_val())

    def __eq__(self, other):
        return (isinstance(other, StringLit) or isinstance(other, Ident))\
            and self.inner_val() == other.inner_val()

    def __str__(self):
        return "StringLit< {} >".format(self.val)

    def into_unmodified_str(self):
        return self.val

    def inner_val(self):
        return self.val.strip()[1:-1]


class Ident(ASTNode):
    def __init__(self, span, val):
        """
        Construct an Ident ast node.
        :type span: Span
        :param span: Span for this identifier
        :type val: str
        :param val: Value of this identifier
        """
        super(Ident, self).__init__(span)
        self.val = val

    def __hash__(self):
        return hash(self.val)

    def __eq__(self, other):
        return (isinstance(other, StringLit) or isinstance(other, Ident))\
            and self.val == other.inner_val()

    def __str__(self):
        return "Ident< {} >".format(self.val)

    def into_unmodified_str(self):
        return self.val

    def inner_val(self):
        return self.val


class DotPath(ASTNode):
    def __init__(self, span, varname, properties):
        """
        :type span: Span
        :param span: Span for this dotpath.
        :type varname: Ident | StringLit
        :param varname: Name of the variable being changed.
        :type properties: list[StringLit | Ident]
        :param properties: Properties being accessed.
        """
        super(DotPath, self).__init__(span)
        self.varname = varname
        self.properties = properties

    def next_dot_path(self):
        """
        Assuming the properties length is more than zero.
        This returns the dot path where the varname has been
        dropped. So given 'a.b.c' the returned dot path will
        be 'b.c'.

        :rtype: DotPath
        :return: Returns the next dot path.
        """
        return DotPath(
            self.span.new_with_lo(self.properties[0].span.lo),
            self.properties[0],
            self.properties[1:]
        )

    def into_unmodified_str(self):
        arr = [self.varname.into_unmodified_str()]
        arr.extend(map(lambda x: x.into_unmodified_str(), self.properties))
        return '.'.join(arr)

    def __str__(self):
        arr = [str(self.varname)]
        arr.extend(map(lambda x: str(x), self.properties))
        return 'DotPath< {} >'.format('.'.join(arr))

    def __key(self):
        return self.into_unmodified_str().replace('"', '')

    def __eq__(self, other):
        return self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())


class Expr(ASTNode):
    def __init__(self, span, expr_tree):
        """
        Construct an expression
        :type span: Span
        :param span: Span for the expression.
        :type expr_tree: p.ParseResults
        ;:param expr_tree: The tree generated by pyparsing.infixNotation
        """
        super(Expr, self).__init__(span)
        # We don't use this tree at this point.
        # During typecheck we will make sure
        # that the expression can evaluate
        # Finally during evaluation, we will evaluate
        # the final result.
        if isinstance(expr_tree, p.ParseResults):
            expr_tree = expr_tree.asList()
        if isinstance(expr_tree, list):
            for i in xrange(0, len(expr_tree)):
                if isinstance(expr_tree[i], list):
                    expr_tree[i] = Expr(span, expr_tree[i])
            self.expr_tree = expr_tree
        else:
            self.expr_tree = [expr_tree]

    def into_unmodified_str(self):
        # TODO(Joan): reconstruct the original expression
        return 'expression'

    def __str__(self):
        return "Expr< {} >".format(strut.array_to_str(self.expr_tree))


class JsonObj(ASTNode):
    def __init__(self, span, tokens):
        super(JsonObj, self).__init__(span)
        self.props = {}
        last_prop = None
        if len(tokens) > 0:
            for toks in tokens:
                for tok in toks:
                    if isinstance(tok, DotPath):
                        if last_prop is None:
                            last_prop = tok
                        else:
                            self._set_new_prop(last_prop, tok)
                            last_prop = None
                    elif isinstance(tok, StringLit):
                        if last_prop is None:
                            last_prop = tok
                        else:
                            self._set_new_prop(last_prop, tok)
                            last_prop = None
                    elif isinstance(tok, list):
                        if last_prop is None:
                            raise p.ParseFatalException(
                                "Bug Found in JsonObj!"
                            )
                        self._set_new_prop(
                            last_prop,
                            JsonObj.dictify_array(tok)
                        )
                        last_prop = None
                    else:
                        if last_prop is None:
                            raise p.ParseFatalException(
                                "Bug Found in JsonObj!"
                            )
                        self._set_new_prop(last_prop, tok)
                        last_prop = None

    def _set_new_prop(self, prop, token):
        if prop in self.props:
            raise exception.BananaJsonObjShadowingError(self.span, prop.span)
        else:
            self.props[prop] = token

    def into_unmodified_str(self):
        # TODO(Joan): improve this for error reporting
        return str(self.props)

    def __str__(self):
        return "JsonObj< {} >".format(strut.dict_to_str(self.props))

    @staticmethod
    def dictify_array(tok):
        new_array = []
        for el in tok:
            if isinstance(el, list):
                new_array.append(JsonObj.dictify_array(el))
            else:
                new_array.append(el)
        return new_array


def into_connection(ast_node):
    """
    Convert an ast node into a Connection node.
    :type ast_node: Connection | Ident
    :param ast_node: The ast node to convert.
    :rtype: Connection
    :return: Returns a Connection node
    """
    if isinstance(ast_node, Connection):
        return ast_node
    elif isinstance(ast_node, Ident):
        return Connection(
            ast_node.span,
            [ast_node],
            [ast_node]
        )
    else:
        raise p.ParseFatalException("Bug found!")


class Connection(ASTNode):

    def __init__(self, span, inputs=None, outputs=None, connections=None):
        """
        Create a connection object.
        :type span: Span
        :param span: Span for this connection
        :type inputs: list[Ident]
        :param inputs: Input ast nodes of the connection
        :type outputs: list[Ident]
        :param outputs: Outputs nodes
        :type connections: list[(Ident, Ident)]
        :param connections: The list of connections aggregated so far.
        """
        super(Connection, self).__init__(span)
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []
        if connections is None:
            connections = []
        self.inputs = inputs
        self.outputs = outputs
        self.connections = connections
        self.connections_cache = {}
        self._build_connection_cache()

    def connect_to(self, other_con, emitter):
        """
        Connect this connection to the other one.
        After this function has been executed, the other_con
        object can be dropped.
        :type other_con: Connection
        :param other_con: Other connection to connect to.
        :type emitter: emit.Emitter
        :param emitter: Emitter.
        """
        self.span.hi = max(other_con.span.hi, self.span.hi)
        self.span.lo = min(other_con.span.lo, self.span.lo)
        old_outputs = self.outputs
        self.outputs = other_con.outputs

        # Generate new connections
        for old_output in old_outputs:
            for other_input in other_con.inputs:
                self._check_and_connect(old_output, other_input, emitter)

        # Preserve old connections
        self._merge_connections(other_con, emitter)

    def merge_all(self, tokens, emitter):
        """
        Merge all the tokens with this class
        :type tokens: list[list[Connection | Ident]]
        :param tokens: List of list of tokens
        :type emitter: emit.Emitter
        :param emitter: Emitter to report errors
        """
        if len(tokens) == 1:
            if len(tokens[0]) > 0:
                for tok in tokens[0]:
                    other_con = into_connection(tok)
                    self.merge_with(other_con, emitter)

    def merge_and_reset_inputs_outputs(self, other_con, emitter):
        """
        Merge this connection with other_con and reset inputs / outputs
        as they're no longer necessary.
        :type other_con: Connection
        :param other_con: the other connection we are gonna merge with.
        :type emitter: emit.Emitter
        :param emitter: Emitter to report errors
        """
        self.inputs = []
        self.outputs = []
        self._merge_connections(other_con, emitter)

    def merge_with(self, other_con, emitter):
        """
        Merge the provided connection with this one.
        :type other_con: Connection
        :param other_con: Connection to merge with self.
        :type emitter: emit.Emitter
        :param emitter: Emitter to report errors
        """
        def extend(into, iterable, what):
            for other_thing in iterable:
                if len(filter(lambda x: x.val == other_thing.val, into)) > 0:
                    emitter.emit_warning(
                        other_thing.span,
                        "{} {} already present".format(
                            what, other_thing.val
                        )
                    )
                else:
                    into.append(other_thing)
        extend(self.inputs, other_con.inputs, 'Input')
        extend(self.outputs, other_con.outputs, 'Output')
        self._merge_connections(other_con, emitter)

    def _merge_connections(self, other_con, emitter):
        """
        Merge only the connections field from other_con into self.
        :type other_con: Connection
        :param other_con: Connection to merge with self.
        :type emitter: emit.Emitter
        :param emitter: Emitter to report errors
        """
        for ident_from, ident_to in other_con.connections:
            self._check_and_connect(ident_from, ident_to, emitter)

    def _check_and_connect(self, ident_from, ident_to, emitter):
        """
        Check if the connection does not already exists and if it does not,
        add it to the list of connections. Otherwise report a warning and
        do nothing.

        :type ident_from: Ident
        :param ident_from: The 'From' node of the directed edge.
        :type ident_to: Ident
        :param ident_to: The 'To' node of the directed edge we are creating.
        :type emitter: emit.Emitter
        :param emitter: Emitter to report errors.
        """
        if ident_from.val in self.connections_cache:
            if ident_to.val in self.connections_cache[ident_from.val]:
                emitter.emit_warning(
                    ident_to.span,
                    "Connection from '{}' to '{}'"
                    " is already present"
                    .format(ident_from.val, ident_to.val)
                )
                return
            self.connections_cache[ident_from.val].append(ident_to.val)
        else:
            self.connections_cache[ident_from.val] = [ident_to.val]
        self.connections.append((ident_from, ident_to))

    def _build_connection_cache(self):
        """
        Build a cache of connections keyed by where they start from.
        """
        for ident_from, ident_to in self.connections:
            if ident_from.val not in self.connections_cache:
                self.connections_cache[ident_from.val] = []
            if ident_to.val not in self.connections_cache:
                self.connections_cache[ident_to.val] = []
            self.connections_cache[ident_from.val].append(ident_to.val)
        # Sanity check
        for _, vals in self.connections_cache:
            if len(set(vals)) != len(vals):
                raise p.ParseFatalException("Bug found in Connection!!")

    def into_unmodified_str(self):
        # TODO(Joan): improve this
        return "connection"

    def __str__(self):
        res = "Connection<"
        res += " {} ".format(map(lambda (x, y): (str(x), str(y)),
                                 self.connections))
        res += ">"
        return res


class Assignment(ASTNode):

    def __init__(self, span, dot_path, value):
        """
        Construct an assignment AST node.
        :type span: Span
        :param span: the span of the assignment.
        :type dot_path: DotPath
        :param dot_path: the left hand side of the assignment.
        :type value: Component | Number | StringLit | JsonObj | DotPath | Expr
        :param value: the right hand side of the assignment.
        """
        super(Assignment, self).__init__(span)
        if (isinstance(value, Component) or
            isinstance(value, JsonObj) or
            isinstance(value, Number) or
            isinstance(value, StringLit) or
            isinstance(value, Ident) or
            isinstance(value, DotPath) or
                isinstance(value, Expr)) and\
                isinstance(dot_path, DotPath):
            self.lhs = dot_path
            self.rhs = value
        else:
            raise exception.BananaGrammarBug(
                'Impossible assignment found with'
                ' left hand side: {} and'
                ' right hand side: {}'
                .format(type(dot_path), type(value))
            )

    def into_unmodified_str(self):
        return "{} = {}".format(self.lhs.into_unmodified_str(),
                                self.rhs.into_unmodified_str())

    def __str__(self):
        return "{} = {}".format(str(self.lhs), str(self.rhs))


class ComponentCtorArg(ASTNode):

    def __init__(self, span, value, arg_name=None):
        """
        Construct an argument for a component ctor
        :type span: Span
        :param span: Span of the argument.
        :type value: Number | StringLit | JsonObj | DotPath | Expr
        :param value: Value for the argument
        :type arg_name: Ident
        :param arg_name: Name of the argument
        """
        super(ComponentCtorArg, self).__init__(span)
        if (isinstance(value, JsonObj) or
            isinstance(value, Number) or
            isinstance(value, StringLit) or
            isinstance(value, Ident) or
            isinstance(value, DotPath) or
                isinstance(value, Expr)) and (
                isinstance(arg_name, Ident) or
                arg_name is None):
            self.arg_name = arg_name
            self.value = value
        else:
            # This code should be unreachable.
            # The grammar as defined should prevent us from
            # seeing an arg value or a value of the incorrect type
            raise exception.BananaGrammarBug(
                'Impossible constructor argument found with'
                ' left hand side: {} and'
                ' right hand side: {}'
                .format(type(arg_name), type(value))
            )

    def into_unmodified_str(self):
        return "{} = {}".format(self.arg_name.into_unmodified_str(),
                                self.value.into_unmodified_str())

    def __str__(self):
        if self.arg_name is not None:
            return "{} = {}".format(self.arg_name, self.value)
        else:
            return "{}".format(self.value)


class Component(ASTNode):

    def __init__(self, span, type_name=None, args=None):
        """
        Construct a component
        :type span: Span
        :param span: Span of this component
        :type type_name: Ident
        :param type_name: Name of this component
        :type args: list[ComponentCtorArg]
        :param args: List of arguments
        """
        super(Component, self).__init__(span)
        if args is None:
            args = []
        self.type_name = type_name
        self.args = args

    def set_ctor(self, type_name):
        """
        Set the constructor name of that component
        :type type_name: Ident
        :param type_name: Name of that constructor
        """
        self.type_name = type_name

    def add_arg(self, arg):
        """
        Add an argument to that component constructor.
        :type arg: ComponentCtorArg
        :param arg: Argument to add to that component.
        """
        self.args.append(arg)

    def into_unmodified_str(self):
        return self.type_name.into_unmodified_str() + "(" + \
            ', '.join(map(lambda x: x.into_unmodified_str(), self.args)) +\
            ")"

    def __str__(self):
        res = ""
        res += "Component {"
        res += "    type_name:  {},".format(self.type_name)
        arr = ', '.join(map(lambda x: str(x), self.args))
        res += "    args: {}".format("[" + arr + "]")
        res += "}"
        return res
