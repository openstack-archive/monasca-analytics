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

import pyparsing as p

import monasca_analytics.banana.emitter as emit
import monasca_analytics.banana.grammar.ast as ast
import monasca_analytics.banana.grammar.const as const
import monasca_analytics.exception.banana as exception


# This file describe the grammar for the banana config file.
# It make use of one sub grammar for certain configuration
# that requires expressions (see expression.py file)


def banana_grammar(emitter=emit.PrintEmitter()):
    """
    Generate a banana parser that can be then used to
    parse a banana content. It build an AST on which
    operation can then be applied.
    :return: Return a banana parser
    :rtype: BananaScopeParser
    """
    # Should debug
    debug_grammar = False

    # Actions
    def action_str_lit(s, l, t):
        return ast.StringLit(ast.make_span(s, l, t), t[0])

    def action_num_lit(s, l, t):
        return ast.Number(ast.make_span(s, l, t), t[0])

    def action_ident(s, l, t):
        return ast.Ident(ast.make_span(s, l, t), t[0])

    def action_expr(s, l, t):
        if len(t) != 1:
            raise exception.BananaGrammarBug(
                'Bug found in the grammar for expression,'
                ' Please report this bug.'
            )
        if isinstance(t[0], ast.Expr):
            return t[0]
        return ast.Expr(ast.make_span(s, l, t), t[0])

    def action_dot_path(s, l, t):
        # First token is the name of the variable
        # The rest is the property path
        if isinstance(t[0], ast.StringLit) and len(t[1:]) == 0:
            return t[0]
        return ast.DotPath(ast.make_span(s, l, t), t[0], t[1:])

    def action_json_obj(s, l, t):
        return ast.JsonObj(ast.make_span(s, l, t), t)

    def action_parse_ctor_arg(s, l, t):
        if len(t) > 1:
            return ast.ComponentCtorArg(ast.make_span(s, l, t), t[1], t[0])
        else:
            return ast.ComponentCtorArg(ast.make_span(s, l, t), t[0])

    def action_parse_comp_ctor(s, l, tokens):
        comp = ast.Component(ast.make_span(s, l, tokens))
        for tok in tokens:
            if isinstance(tok, ast.Ident):
                comp.set_ctor(tok)
            elif isinstance(tok, ast.ComponentCtorArg):
                comp.add_arg(tok)
            else:
                raise exception.BananaGrammarBug(
                    'Bug found in the grammar, Please report this bug'
                )
        return comp

    def action_assignment(s, l, t):
        return ast.Assignment(ast.make_span(s, l, t), t[0], t[1])

    def action_create_connections(s, l, t):
        ast_conn = ast.into_connection(t[0])
        ast_conn.span = ast.make_span(s, l, t)
        for i in range(1, len(t)):
            next_conn = ast.into_connection(t[i])
            ast_conn.connect_to(next_conn, emitter)
        return ast_conn

    def action_merge_connections(s, l, t):
        ast_conn = ast.Connection(ast.make_span(s, l, t))
        ast_conn.merge_all(t, emitter)
        return ast_conn

    def action_root_ast(s, l, tokens):
        root = ast.BananaFile(emitter)
        for tok in tokens:
            if isinstance(tok, ast.Assignment):
                if isinstance(tok.rhs, ast.Component):
                    root.add_component_ctor(tok.lhs, tok.rhs)
                else:
                    root.add_assignment(tok.lhs, tok.rhs)
            elif isinstance(tok, ast.Connection):
                root.add_connections(tok)
            else:
                raise exception.BananaGrammarBug(
                    'Bug found in the grammar, Please report this bug.'
                )
        return root

    # TODO(Joan): Remove once it is no longer needed
    def print_stmt(s, l, t):
        print("\nPRINT AST")
        print(l, map(lambda x: str(x), t))
        print("END PRINT AST\n")

    def action_unimplemented(s, l, t):
        raise exception.BananaGrammarBug("unimplemented code reached")

    # Tokens
    equals = p.Literal("=").suppress().setName('"="').setDebug(debug_grammar)
    arrow = p.Literal("->").suppress().setName('"->"').setDebug(debug_grammar)
    lbra = p.Literal("[").suppress().setName('"["').setDebug(debug_grammar)
    rbra = p.Literal("]").suppress().setName('"]"').setDebug(debug_grammar)
    colon = p.Literal(":").suppress().setName('":"')
    comma = p.Literal(",").suppress().setName(",")
    less = p.Literal("<").suppress().setName('"<"')
    greater = p.Literal(">").suppress().setName('">"')
    lbrace = p.Literal("{").suppress().setName('"{"').setDebug(debug_grammar)
    rbrace = p.Literal("}").suppress().setName('"}"').setDebug(debug_grammar)
    lpar = p.Literal("(").suppress().setName('"("')
    rpar = p.Literal(")").suppress().setName('")"')

    # Keywords
    ing = p.Literal("ing").suppress()
    imp = p.Literal("import").suppress()
    fro = p.Literal("from").suppress()

    # String Literal, Numbers, Identifiers
    string_lit = p.quotedString()\
        .setParseAction(action_str_lit)\
        .setName(const.STRING_LIT)
    number_lit = p.Regex(r'\d+(\.\d*)?([eE]\d+)?')\
        .setParseAction(action_num_lit)\
        .setName(const.NUMBER)
    ident = p.Word(p.alphas + "_", p.alphanums + "_")\
        .setParseAction(action_ident)\
        .setName(const.IDENT)

    # Path for properties
    dot_prop = ident | string_lit
    dot_path = p.delimitedList(dot_prop, ".")\
        .setParseAction(action_dot_path)\
        .setName(const.DOT_PATH)\
        .setDebug(debug_grammar)

    # Expressions

    # Here to simplify the logic, we can match directly
    # against ident and string_lit to avoid having to deal
    # only with dot_path. It also allow to remove the confusion
    # where '"a"' could be interpreted as a dot_path and would thus
    # be the same as 'a'. With the following, the first we
    # always be type-checked as a String whereas the latter will
    # be as the type of the variable.
    expr = p.infixNotation(number_lit | dot_path, [
        (p.oneOf('* /'), 2, p.opAssoc.LEFT),
        (p.oneOf('+ -'), 2, p.opAssoc.LEFT),
    ], lpar=lpar, rpar=rpar)
    expr.setParseAction(action_expr)\
        .setName(const.EXPR)\
        .setDebug(debug_grammar)

    # Json-like object (value are much more)
    json_obj = p.Forward()
    json_value = p.Forward()
    json_array = p.Group(
        lbra + p.Optional(p.delimitedList(json_value)) + rbra
    )
    json_array.setDebug(debug_grammar)
    json_array.setName(const.JSON_ARRAY)
    json_value <<= expr | json_obj | json_array
    json_value.setDebug(debug_grammar)\
        .setName(const.JSON_VALUE)
    json_members = p.delimitedList(p.Group(dot_path + colon - json_value)) +\
        p.Optional(comma)
    json_members.setDebug(debug_grammar)\
        .setName(const.JSON_MEMBERS)
    json_obj <<= p.Dict(lbrace + p.Optional(json_members) - rbrace)
    json_obj.setParseAction(action_json_obj)\
        .setName(const.JSON_OBJ)\
        .setDebug(debug_grammar)

    # Component constructor
    arg = (ident + equals - (expr | json_obj)) | expr | json_obj
    arg.setParseAction(action_parse_ctor_arg)
    params = p.delimitedList(arg)
    comp_ctor = ident + lpar - p.Optional(params) + rpar
    comp_ctor.setParseAction(action_parse_comp_ctor)\
        .setName(const.COMP_CTOR)\
        .setDebug(debug_grammar)

    # Assignments
    assignment = dot_path + equals - (comp_ctor | expr | json_obj)
    assignment.setParseAction(action_assignment)

    # Connections
    connection = p.Forward()
    array_of_connection = p.Group(
        lbra + p.Optional(p.delimitedList(connection)) + rbra
    )
    array_of_connection.setParseAction(action_merge_connections)
    last_expr = ident | array_of_connection
    this_expr = p.Forward()
    match_expr = p.FollowedBy(last_expr + arrow - last_expr) + \
        (last_expr + p.OneOrMore(arrow - last_expr))
    this_expr <<= match_expr | last_expr
    connection <<= this_expr

    match_expr.setDebug(debug_grammar)\
        .setName(const.CONNECTION) \
        .setParseAction(action_create_connections)

    # Definitions
    definition = ing - less - string_lit - greater - ident - lbrace - rbrace
    definition.setDebug(debug_grammar)\
        .setName(const.DEFINITION)\
        .setParseAction(action_unimplemented)

    # Import directive
    module_def = (imp - ident) | fro - ident - imp - ident
    module_def.setDebug(debug_grammar)\
        .setName(const.MOD_IMPORT)\
        .setParseAction(action_unimplemented)

    # Comments
    comments = "#" + p.restOfLine

    statement = assignment | \
        match_expr | \
        definition | \
        module_def

    statement.setName(const.STATEMENT)
    statement.setDebug(debug_grammar)
    statement.setParseAction(print_stmt)

    # Grammar
    grammar = p.OneOrMore(statement).ignore(comments)
    grammar.setParseAction(action_root_ast)

    return BananaScopeParser(grammar)


class BananaScopeParser(object):
    """
    Aggregate and resolve conflicts as everything was define
    within the same scope. Usefull for have cpp "include"-like
    functionality when importing another file.
    """

    def __init__(self, grammar):
        self._grammar = grammar

    def parse(self, string):
        """
        Parse the given input string.
        :type string: str
        :param string: Input string.
        :rtype: ast.BananaFile
        :return: Returns the ast root.
        """
        tree = self._grammar.parseString(string, parseAll=True)[0]
        return tree
