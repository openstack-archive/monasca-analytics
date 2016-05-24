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

import pyparsing as p

from main.dsl import const


EQUALS = p.Literal("=").suppress()
CONNECT = p.Literal("->").suppress()
DISCONNECT = p.Literal("!->").suppress()
LPAREN = p.Literal("(").suppress()
RPAREN = p.Literal(")").suppress()
LOAD = p.CaselessKeyword("load").suppress()
SAVE = p.CaselessKeyword("save").suppress()
REMOVE = p.CaselessKeyword("rm").suppress()
PRINT = p.CaselessKeyword("print").suppress()
LIST = p.CaselessKeyword("list").suppress()
HELP = p.CaselessKeyword("help").suppress()
DOT = p.Literal(".").suppress()
VARNAME = p.Word(p.alphas+"_", p.alphanums+"_")
PARAMETER = p.Word(p.alphanums+"_-")
MODULE_NAME = p.Word(p.alphanums+"_-")
VALUE = p.Word(p.alphanums+"_-.")
PATH = p.Word(p.alphanums+"_-/\.")

cmd_create = (VARNAME + EQUALS + MODULE_NAME)
cmd_connect = (VARNAME + CONNECT + VARNAME)
cmd_disconnect = (VARNAME + DISCONNECT + VARNAME)
cmd_modify = (VARNAME + p.OneOrMore(DOT + PARAMETER) + EQUALS + VALUE)
cmd_load = (LOAD + p.Optional(LPAREN) + PATH + p.Optional(RPAREN))
cmd_save = (SAVE + p.Optional(LPAREN) + p.Optional(RPAREN))
cmd_save_as = (SAVE + p.Optional(LPAREN) + PATH + p.Optional(RPAREN))
cmd_remove = (REMOVE + p.Optional(LPAREN) + VARNAME + p.Optional(RPAREN))
cmd_print = (PRINT + p.Optional(LPAREN) + p.Optional(VARNAME) +
             p.Optional(RPAREN))
cmd_list = (LIST + p.Optional(LPAREN) + p.Optional(VARNAME) +
            p.Optional(RPAREN))
cmd_help = (HELP + p.Optional(LPAREN) + p.Optional(RPAREN))

bnfLine = cmd_create(const.CREATE) | cmd_connect(const.CONNECT) |\
    cmd_disconnect(const.DISCONNECT) | cmd_load(const.LOAD) |\
    cmd_save_as(const.SAVE_AS) | cmd_save(const.SAVE) |\
    cmd_remove(const.REMOVE) | cmd_modify(const.MODIFY) |\
    cmd_print(const.PRINT) | cmd_list(const.LIST) | cmd_help(const.HELP)

bnfComment = "#" + p.restOfLine

bnf = p.OneOrMore(p.Group(bnfLine))
bnf.ignore(bnfComment)


def get_parser():
    return bnf
