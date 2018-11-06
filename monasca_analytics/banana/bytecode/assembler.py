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

# This file is an adaptation of BytecodeAssembler:
#
#   http://peak.telecommunity.com/DevCenter/BytecodeAssembler#toc
#
# It has been adapted to match the requirements of monasca_analytics

import sys

from array import array
from decorators import decorate_assignment
from dis import cmp_op
from dis import EXTENDED_ARG
from dis import hasfree
from dis import hasjabs
from dis import hasjrel
from dis import haslocal
from dis import hasname
from dis import HAVE_ARGUMENT
from dis import opname
from symbols import Symbol
from types import CodeType
from types import FunctionType


opcode = {}
for op in range(256):
    _name = opname[op]
    if _name.startswith('<'):
        continue
    if _name.endswith('+0'):
        opcode[_name[:-2]] = op
    opcode[_name] = op

# globals().update(opcode)  # opcodes are now importable at will

# Flags from code.h
CO_OPTIMIZED = 0x0001      # use LOAD/STORE_FAST instead of _NAME
CO_NEWLOCALS = 0x0002      # only cleared for module/exec code
CO_VARARGS = 0x0004
CO_VARKEYWORDS = 0x0008
CO_NESTED = 0x0010      # ???
CO_GENERATOR = 0x0020
CO_NOFREE = 0x0040      # set if no free or cell vars
CO_GENERATOR_ALLOWED = 0x1000      # unused
CO_FUTURE_DIVISION = 0x2000
CO_FUTURE_ABSOLUTE_IMPORT = 0x4000      # Python 2.5+ only
CO_FUTURE_WITH_STATEMENT = 0x8000      # Python 2.5+ only

# opcode
LOAD_DEREF = opcode["LOAD_DEREF"]
STORE_DEREF = opcode["STORE_DEREF"]
LOAD_FAST = opcode["LOAD_FAST"]
STORE_FAST = opcode["STORE_FAST"]
DELETE_FAST = opcode["DELETE_FAST"]
YIELD_VALUE = opcode["YIELD_VALUE"]
LOAD_CONST = opcode["LOAD_CONST"]
CALL_FUNCTION = opcode["CALL_FUNCTION"]
CALL_FUNCTION_VAR = opcode["CALL_FUNCTION_VAR"]
CALL_FUNCTION_KW = opcode["CALL_FUNCTION_KW"]
CALL_FUNCTION_VAR_KW = opcode["CALL_FUNCTION_VAR_KW"]
BUILD_TUPLE = opcode["BUILD_TUPLE"]
BUILD_LIST = opcode["BUILD_LIST"]
UNPACK_SEQUENCE = opcode["UNPACK_SEQUENCE"]
RETURN_VALUE = opcode["RETURN_VALUE"]
BUILD_SLICE = opcode["BUILD_SLICE"]
DUP_TOPX = opcode["DUP_TOPX"]
RAISE_VARARGS = opcode["RAISE_VARARGS"]
MAKE_FUNCTION = opcode["MAKE_FUNCTION"]
MAKE_CLOSURE = opcode["MAKE_CLOSURE"]
FOR_ITER = opcode["FOR_ITER"]
JUMP_IF_TRUE_OR_POP = opcode["JUMP_IF_TRUE_OR_POP"]
JUMP_IF_FALSE_OR_POP = opcode["JUMP_IF_FALSE_OR_POP"]
JUMP_FORWARD = opcode["JUMP_FORWARD"]
JUMP_ABSOLUTE = opcode["JUMP_ABSOLUTE"]
SETUP_EXCEPT = opcode["SETUP_EXCEPT"]
SETUP_FINALLY = opcode["SETUP_FINALLY"]
SETUP_LOOP = opcode["SETUP_LOOP"]
BREAK_LOOP = opcode["BREAK_LOOP"]
CONTINUE_LOOP = opcode["CONTINUE_LOOP"]
POP_BLOCK = opcode["POP_BLOCK"]
LIST_APPEND = opcode["LIST_APPEND"]
COMPARE_OP = opcode["COMPARE_OP"]
LOAD_NAME = opcode["LOAD_NAME"]
STORE_NAME = opcode["STORE_NAME"]
DELETE_NAME = opcode["DELETE_NAME"]

fast_to_deref = {
    LOAD_FAST: LOAD_DEREF,
    STORE_FAST: STORE_DEREF,
}

deref_to_deref = dict([(k, k) for k in hasfree])


def with_name(f, name):
    try:
        f.__name__ = name
        return f
    except (TypeError, AttributeError):
        return FunctionType(
            f.func_code, f.func_globals, name, f.func_defaults, f.func_closure
        )


class Const(object):
    """Wrapper to ensure constants are hashable even if mutable"""

    __slots__ = 'value', 'hash', 'hashable'

    def __init__(self, value_):
        self.value = value_
        try:
            self.hash = hash(value_)
        except TypeError:
            self.hash = hash(id(value_))
            self.hashable = False
        else:
            self.hashable = True

    def __repr__(self):
        return "Const(%s)" % repr(self.value)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        if type(other) is not Const:
            return False
        if self.hashable:
            return self.value == other.value
        else:
            return self.value is other.value

    def __ne__(self, other):
        return not self == other

    def __call__(self, code):
        code.LOAD_CONST(self.value)


class Node(tuple):
    """Base class for AST nodes"""
    __slots__ = []


def nodetype(*mixins, **kw):

    def callback(frame, name, func, old_locals):
        def __new__(cls, *args, **kw):
            result = func(*args, **kw)
            if type(result) is tuple:
                return tuple.__new__(cls, (cls,) + result)
            else:
                return result

        def __repr__(self):
            r = self.__class__.__name__ + tuple.__repr__(self[1:])
            if len(self) == 2:
                return r[:-2] + ')'  # nix trailing ','
            return r

        def __call__(self, code):
            return func(*(self[1:] + (code,)))

        import inspect
        args = inspect.getargspec(func)[0]

        d = dict(
            __new__=__new__, __repr__=__repr__, __doc__=func.__doc__,
            __module__=func.__module__, __args__=args, __slots__=[],
            __call__=__call__
        )
        for p, a in enumerate(args[:-1]):    # skip 'code' argument
            if isinstance(a, str):
                d[a] = property(lambda self, p=p + 1: self[p])

        d.update(kw)
        return type(name, mixins + (Node,), d)

    return decorate_assignment(callback)


@nodetype()
def Local(name, code=None):
    if code is None:
        return name,
    if name in code.co_cellvars or name in code.co_freevars:
        return code.LOAD_DEREF(name)
    elif code.co_flags & CO_OPTIMIZED:
        return code.LOAD_FAST(name)
    else:
        return code.LOAD_NAME(name)


@nodetype()
def Getattr(ob, name, code=None):
    try:
        name = const_value(name)
    except NotAConstant:
        return Call(Const(getattr), [ob, name])
    if code is None:
        return fold_args(Getattr, ob, name)
    code(ob)
    code.LOAD_ATTR(name)


@nodetype()
def Call(fn, args=(), kwargs=(), star=None, dstar=None, fold=True, code=None):
    if code is None:
        data = (
            fn, tuple(args), tuple(kwargs), star or (), dstar or (), fold
        )
        if fold and (args or kwargs or star or dstar):
            return fold_args(Call, *data)
        else:
            return data

    code(fn, *args)
    for k, v in kwargs:
        code(k, v)

    argc = len(args)
    kwargc = len(kwargs)

    if star:
        if dstar:
            code(star, dstar)
            return code.CALL_FUNCTION_VAR_KW(argc, kwargc)
        else:
            code(star)
            return code.CALL_FUNCTION_VAR(argc, kwargc)
    else:
        if dstar:
            code(dstar)
            return code.CALL_FUNCTION_KW(argc, kwargc)
        else:
            return code.CALL_FUNCTION(argc, kwargc)


class _Pass(Symbol):
    def __call__(self, code=None):
        pass

    def __nonzero__(self):
        return False
Pass = _Pass('Pass', __name__)


class NotAConstant(Exception):
    """The supplied value is not a constant expression tree"""


def const_value(value_):
    """Return the constant value -- if any -- of an expression tree

    Raises NotAConstant if the value or any child of the value are
    not constants.
    """
    t = type(value_)
    if t is Const:
        value_ = value_.value
    elif t is tuple:
        t = tuple(map(const_value, value_))
        if t == value_:
            return value_
        return t
    elif generate_types.get(t) != Code.LOAD_CONST:
        raise NotAConstant(value_)
    return value_


def fold_args(f, *args):
    """Return a folded ``Const`` or an argument tuple"""

    try:
        for arg in args:
            if arg is not Pass and arg is not None:
                const_value(arg)
    except NotAConstant:
        return args
    else:
        c = Code()
        f(*args + (c,))
        c.RETURN_VALUE()
        return Const(eval(c.code()))


@nodetype()
def LocalAssign(name, code=None):
    if code is None:
        return name,
    if name in code.co_cellvars or name in code.co_freevars:
        return code.STORE_DEREF(name)
    elif code.co_flags & CO_OPTIMIZED:
        return code.STORE_FAST(name)
    else:
        return code.STORE_NAME(name)


class Code(object):
    co_argcount = 0
    co_stacksize = 0
    co_flags = CO_OPTIMIZED | CO_NEWLOCALS  # typical usage
    co_filename = '<generated code>'
    co_name = '<lambda>'
    co_firstlineno = 0
    co_freevars = ()
    co_cellvars = ()
    _last_lineofs = 0
    _ss = 0
    _tmp_level = 0

    def __init__(self):
        self.co_code = array('B')
        self.co_consts = [None]
        self.co_names = []
        self.co_varnames = []
        self.co_lnotab = array('B')
        self.emit = self.co_code.append
        self.blocks = []
        self.stack_history = []

    def emit_arg(self, op, arg):
        emit = self.emit
        if arg > 0xFFFF:
            emit(EXTENDED_ARG)
            emit((arg >> 16) & 255)
            emit((arg >> 24) & 255)
        emit(op)
        emit(arg & 255)
        emit((arg >> 8) & 255)

    def locals_written(self):
        vn = self.co_varnames
        hl = dict.fromkeys([STORE_FAST, DELETE_FAST])
        return dict.fromkeys([vn[arg] for ofs, op, arg in self if op in hl])

    def set_lineno(self, lno):
        if not self.co_firstlineno:
            self.co_firstlineno = self._last_line = lno
            return

        append = self.co_lnotab.append
        incr_line = lno - self._last_line
        incr_addr = len(self.co_code) - self._last_lineofs
        if not incr_line:
            return

        assert incr_addr >= 0 and incr_line >= 0

        while incr_addr > 255:
            append(255)
            append(0)
            incr_addr -= 255

        while incr_line > 255:
            append(incr_addr)
            append(255)
            incr_line -= 255
            incr_addr = 0

        if incr_addr or incr_line:
            append(incr_addr)
            append(incr_line)

        self._last_line = lno
        self._last_lineofs = len(self.co_code)

    def YIELD_VALUE(self):
        self.stackchange(stack_effects[YIELD_VALUE])
        self.co_flags |= CO_GENERATOR
        return self.emit(YIELD_VALUE)

    def LOAD_CONST(self, const):
        self.stackchange(0, 1)
        pos = 0
        hashable = True
        try:
            hash(const)
        except TypeError:
            hashable = False
        while 1:
            try:
                arg = self.co_consts.index(const, pos)
                it = self.co_consts[arg]
            except ValueError:
                arg = len(self.co_consts)
                self.co_consts.append(const)
                break
            else:
                if type(it) is type(const) and (hashable or it is const):
                    break
            pos = arg + 1
            continue
        return self.emit_arg(LOAD_CONST, arg)

    def CALL_FUNCTION(self, argc=0, kwargc=0, op=CALL_FUNCTION, extra=0):
        self.stackchange(1 + argc + 2 * kwargc + extra, 1)
        emit = self.emit
        emit(op)
        emit(argc)
        emit(kwargc)

    def CALL_FUNCTION_VAR(self, argc=0, kwargc=0):
        self.CALL_FUNCTION(
            argc,
            kwargc,
            CALL_FUNCTION_VAR,
            1)  # 1 for *args

    def CALL_FUNCTION_KW(self, argc=0, kwargc=0):
        self.CALL_FUNCTION(
            argc,
            kwargc,
            CALL_FUNCTION_KW,
            1)  # 1 for **kw

    def CALL_FUNCTION_VAR_KW(self, argc=0, kwargc=0):
        self.CALL_FUNCTION(
            argc,
            kwargc,
            CALL_FUNCTION_VAR_KW,
            2)  # 2 *args,**kw

    def BUILD_TUPLE(self, count):
        self.stackchange(count, 1)
        self.emit_arg(BUILD_TUPLE, count)

    def BUILD_LIST(self, count):
        self.stackchange(count, 1)
        self.emit_arg(BUILD_LIST, count)

    def UNPACK_SEQUENCE(self, count):
        self.stackchange(1, count)
        self.emit_arg(UNPACK_SEQUENCE, count)

    def RETURN_VALUE(self):
        self.stackchange(1, 0)
        self.emit(RETURN_VALUE)
        self.stack_unknown()

    def BUILD_SLICE(self, count):
        assert count in (2, 3), "Invalid number of arguments for BUILD_SLICE"
        self.stackchange(count, 1)
        self.emit_arg(BUILD_SLICE, count)

    def DUP_TOPX(self, count):
        self.stackchange(count, count * 2)
        self.emit_arg(DUP_TOPX, count)

    def RAISE_VARARGS(self, argc):
        assert 0 <= argc <= 3, "Invalid number of arguments for RAISE_VARARGS"
        self.stackchange(argc, 0)
        self.emit_arg(RAISE_VARARGS, argc)

    def MAKE_FUNCTION(self, ndefaults):
        self.stackchange(1 + ndefaults, 1)
        self.emit_arg(MAKE_FUNCTION, ndefaults)

    def MAKE_CLOSURE(self, ndefaults, freevars):
        if sys.version >= '2.5':
            freevars = 1
        self.stackchange(1 + freevars + ndefaults, 1)
        self.emit_arg(MAKE_CLOSURE, ndefaults)

    def here(self):
        return len(self.co_code)

    def set_stack_size(self, size):
        if size < 0:
            raise AssertionError("Stack underflow")
        if size > self.co_stacksize:
            self.co_stacksize = size
        bytes = len(self.co_code) - len(self.stack_history) + 1
        if bytes > 0:
            self.stack_history.extend([self._ss] * bytes)
        self._ss = size

    def get_stack_size(self):
        return self._ss

    stack_size = property(get_stack_size, set_stack_size)

    def stackchange(self, inputs, outputs):
        if self._ss is None:
            raise AssertionError("Unknown stack size at this location")
        self.stack_size -= inputs  # check underflow
        self.stack_size += outputs  # update maximum height

    def stack_unknown(self):
        self._ss = None

    def branch_stack(self, location, expected):
        if location >= len(self.stack_history):
            if location > len(self.co_code):
                raise AssertionError("Forward-looking stack prediction!",
                                     location, len(self.co_code)
                                     )
            actual = self.stack_size
            if actual is None:
                self.stack_size = actual = expected
                self.stack_history[location] = actual
        else:
            actual = self.stack_history[location]
            if actual is None:
                self.stack_history[location] = actual = expected

        if actual != expected:
            raise AssertionError(
                "Stack level mismatch: actual=%s expected=%s"
                % (actual, expected)
            )

    def jump(self, op, arg=None):
        def jump_target(offset):
            target = offset
            if op not in hasjabs:
                target = target - (posn + 3)
                if target < 0:
                    raise AssertionError("Relative jumps can't go backwards")
                if target > 0xFFFF:
                    target = offset - (posn + 6)
            return target

        def backpatch(offset):
            target = jump_target(offset)
            if target > 0xFFFF:
                raise AssertionError("Forward jump span must be <64K bytes")
            self.patch_arg(posn, 0, target)
            self.branch_stack(offset, old_level)

        if op == FOR_ITER:
            old_level = self.stack_size = self.stack_size - 1
            self.stack_size += 2
        else:
            old_level = self.stack_size
        self.stack_size -= (op in (JUMP_IF_TRUE_OR_POP, JUMP_IF_FALSE_OR_POP))
        posn = self.here()
        if arg is not None:
            self.emit_arg(op, jump_target(arg))
            self.branch_stack(arg, old_level)
            lbl = None
        else:
            self.emit_arg(op, 0)

            def lbl(code=None):
                backpatch(self.here())
        if op in (JUMP_FORWARD, JUMP_ABSOLUTE, CONTINUE_LOOP):
            self.stack_unknown()
        return lbl

    def COMPARE_OP(self, op):
        self.stackchange(2, 1)
        self.emit_arg(COMPARE_OP, compares[op])

    def setup_block(self, op):
        jmp = self.jump(op)
        self.blocks.append((op, self.stack_size, jmp))
        return jmp

    def SETUP_EXCEPT(self):
        ss = self.stack_size
        self.stack_size = ss + 3  # simulate the level at "except:" time
        self.setup_block(SETUP_EXCEPT)
        self.stack_size = ss  # restore the current level

    def SETUP_FINALLY(self):
        ss = self.stack_size
        self.stack_size = ss + 3  # allow for exceptions
        self.stack_size = ss + 1  # simulate the level after the None is pushed
        self.setup_block(SETUP_FINALLY)
        self.stack_size = ss  # restore original level

    def SETUP_LOOP(self):
        self.setup_block(SETUP_LOOP)

    def POP_BLOCK(self):
        if not self.blocks:
            raise AssertionError("Not currently in a block")

        why, level, fwd = self.blocks.pop()
        self.emit(POP_BLOCK)

        if why != SETUP_LOOP:
            if why == SETUP_FINALLY:
                self.LOAD_CONST(None)
                fwd()
            else:
                self.stack_size = level - 3  # stack level resets here
                else_ = self.JUMP_FORWARD()
                fwd()
                return else_
        else:
            return fwd

    if 'JUMP_IF_TRUE_OR_POP' not in opcode:
        def JUMP_IF_TRUE_OR_POP(self, address=None):
            lbl = self.JUMP_IF_TRUE(address)
            self.POP_TOP()
            return lbl

        globals()['JUMP_IF_TRUE_OR_POP'] = -1

    if 'JUMP_IF_FALSE_OR_POP' not in opcode:
        def JUMP_IF_FALSE_OR_POP(self, address=None):
            lbl = self.JUMP_IF_FALSE(address)
            self.POP_TOP()
            return lbl

        globals()['JUMP_IF_FALSE_OR_POP'] = -1

    if 'JUMP_IF_TRUE' not in opcode:
        def JUMP_IF_TRUE(self, address=None):
            self.DUP_TOP()
            return self.POP_JUMP_IF_TRUE(address)
    else:
        globals()['POP_JUMP_IF_TRUE'] = -1

    if 'JUMP_IF_FALSE' not in opcode:
        def JUMP_IF_FALSE(self, address=None):
            self.DUP_TOP()
            return self.POP_JUMP_IF_FALSE(address)
    else:
        globals()['POP_JUMP_IF_FALSE'] = -1

    if 'LIST_APPEND' in opcode and LIST_APPEND >= HAVE_ARGUMENT:
        def LIST_APPEND(self, depth):
            self.stackchange(depth + 1, depth)
            self.emit_arg(LIST_APPEND, depth)

    def assert_loop(self):
        for why, level, fwd in self.blocks:
            if why == SETUP_LOOP:
                return
        raise AssertionError("Not inside a loop")

    def BREAK_LOOP(self):
        self.assert_loop()
        self.emit(BREAK_LOOP)
        self.stack_unknown()

    def CONTINUE_LOOP(self, label):
        self.assert_loop()
        if self.blocks[-1][0] == SETUP_LOOP:
            op = JUMP_ABSOLUTE  # more efficient if not in a nested block
        else:
            op = CONTINUE_LOOP
        return self.jump(op, label)

    def __call__(self, *args):
        last = None
        for ob in args:
            if callable(ob):
                last = ob(self)
            else:
                try:
                    f = generate_types[type(ob)]
                except KeyError:
                    raise TypeError("Can't generate", ob)
                else:
                    last = f(self, ob)
        return last

    def return_(self, ob=None):
        return self(ob, Code.RETURN_VALUE)

    @classmethod
    def from_function(cls, function, copy_lineno=False):
        code = cls.from_code(function.func_code, copy_lineno)
        return code

    @classmethod
    def from_code(cls, code, copy_lineno=False):
        import inspect
        self = cls.from_spec(code.co_name, *inspect.getargs(code))
        if copy_lineno:
            self.set_lineno(code.co_firstlineno)
            self.co_filename = code.co_filename
        self.co_freevars = code.co_freevars  # XXX untested!
        return self

    @classmethod
    def from_spec(cls, name='<lambda>', args=(), var=None, kw=None):
        self = cls()
        self.co_name = name
        self.co_argcount = len(args)
        self.co_varnames.extend(args)
        if var:
            self.co_varnames.append(var)
            self.co_flags |= CO_VARARGS
        if kw:
            self.co_varnames.append(kw)
            self.co_flags |= CO_VARKEYWORDS

        def tuple_arg(args):
            self.UNPACK_SEQUENCE(len(args))
            for arg in args:
                if not isinstance(arg, basestring):
                    tuple_arg(arg)
                else:
                    self.STORE_FAST(arg)

        for narg, arg in enumerate(args):
            if not isinstance(arg, basestring):
                dummy_name = '.' + str(narg)
                self.co_varnames[narg] = dummy_name
                self.LOAD_FAST(dummy_name)
                tuple_arg(arg)

        return self

    def patch_arg(self, offset, oldarg, newarg):
        code = self.co_code
        if (oldarg > 0xFFFF) != (newarg > 0xFFFF):
            raise AssertionError("Can't change argument size", oldarg, newarg)
        code[offset + 1] = newarg & 255
        code[offset + 2] = (newarg >> 8) & 255
        if newarg > 0xFFFF:
            newarg >>= 16
            code[offset - 2] = newarg & 255
            code[offset - 1] = (newarg >> 8) & 255

    def nested(self, name='<lambda>', args=(), var=None, kw=None, cls=None):
        if cls is None:
            cls = Code
        code = cls.from_spec(name, args, var, kw)
        code.co_filename = self.co_filename
        return code

    def __iter__(self):
        i = 0
        extended_arg = 0
        code = self.co_code
        n = len(code)
        while i < n:
            op = code[i]
            if op >= HAVE_ARGUMENT:
                oparg = code[i + 1] + code[i + 2] * 256 + extended_arg
                extended_arg = 0
                if op == EXTENDED_ARG:
                    extended_arg = oparg * 65536
                    i += 3
                    continue
                yield i, op, oparg
                i += 3
            else:
                yield i, op, None
                i += 1

    def makefree(self, names):
        nowfree = dict.fromkeys(self.co_freevars)
        newfree = [n for n in names if n not in nowfree]
        if newfree:
            self.co_freevars += tuple(newfree)
            self._locals_to_cells()

    def makecells(self, names):
        nowcells = dict.fromkeys(self.co_cellvars + self.co_freevars)
        newcells = [n for n in names if n not in nowcells]
        if newcells:
            if not (self.co_flags & CO_OPTIMIZED):
                raise AssertionError("Can't use cellvars in unoptimized scope")
            cc = len(self.co_cellvars)
            nc = len(newcells)
            self.co_cellvars += tuple(newcells)
            if self.co_freevars:
                self._patch(
                    deref_to_deref,
                    dict([(n + cc, n + cc + nc) for n in range(
                        len(self.co_freevars))])
                )
            self._locals_to_cells()

    def _locals_to_cells(self):
        freemap = dict(
            [(n, p) for p, n in enumerate(self.co_cellvars + self.co_freevars)]
        )
        argmap = dict(
            [(p, freemap[n]) for p, n in enumerate(self.co_varnames)
             if n in freemap]
        )
        if argmap:
            for ofs, op, arg in self:
                if op == DELETE_FAST and arg in argmap:
                    raise AssertionError(
                        "Can't delete local %r used in nested scope"
                        % self.co_varnames[arg]
                    )
            self._patch(fast_to_deref, argmap)

    def _patch(self, opmap, argmap=None):
        if argmap is None:
            argmap = {}
        code = self.co_code
        for ofs, op, arg in self:
            if op in opmap:
                if arg in argmap:
                    self.patch_arg(ofs, arg, argmap[arg])
                elif arg is not None:
                    continue
                code[ofs] = opmap[op]

    def code(self, parent=None):
        if self.blocks:
            raise AssertionError("%d unclosed block(s)" % len(self.blocks))

        flags = self.co_flags & ~CO_NOFREE
        if parent is not None:
            locals_written = self.locals_written()
            self.makefree([
                n for n in self.co_varnames[
                    self.co_argcount +
                    ((self.co_flags & CO_VARARGS) == CO_VARARGS) +
                    ((self.co_flags & CO_VARKEYWORDS) == CO_VARKEYWORDS):
                ] if n not in locals_written
            ])

        if not self.co_freevars and not self.co_cellvars:
            flags |= CO_NOFREE
        elif parent is not None and self.co_freevars:
            parent.makecells(self.co_freevars)

        return CodeType(
            self.co_argcount, len(self.co_varnames),
            self.co_stacksize, flags, self.co_code.tostring(),
            tuple(self.co_consts), tuple(self.co_names),
            tuple(self.co_varnames),
            self.co_filename, self.co_name, self.co_firstlineno,
            self.co_lnotab.tostring(), self.co_freevars, self.co_cellvars
        )

for op in hasfree:
    if not hasattr(Code, opname[op]):
        def do_free(self, varname, op=op):
            self.stackchange(stack_effects[op][0], stack_effects[op][1])
            try:
                arg = list(self.co_cellvars + self.co_freevars).index(varname)
            except ValueError:
                raise NameError("Undefined free or cell var", varname)
            self.emit_arg(op, arg)
        setattr(Code, opname[op], with_name(do_free, opname[op]))

compares = {}
for value, cmp_name in enumerate(cmp_op):
    compares[value] = value
    compares[cmp_name] = value
compares['<>'] = compares['!=']

for op in hasname:
    if not hasattr(Code, opname[op]):
        def do_name(self, name, op=op):
            self.stackchange(stack_effects[op][0], stack_effects[op][1])
            try:
                arg = self.co_names.index(name)
            except ValueError:
                arg = len(self.co_names)
                self.co_names.append(name)
            self.emit_arg(op, arg)
            if op in (LOAD_NAME, STORE_NAME, DELETE_NAME):
                # Can't use optimized local vars, so reset flags
                self.co_flags &= ~CO_OPTIMIZED
        setattr(Code, opname[op], with_name(do_name, opname[op]))

for op in haslocal:
    if not hasattr(Code, opname[op]):
        def do_local(self, varname, op=op):
            if not self.co_flags & CO_OPTIMIZED:
                raise AssertionError(
                    "co_flags must include CO_OPTIMIZED to use fast locals"
                )
            self.stackchange(stack_effects[op][0], stack_effects[op][1])
            try:
                arg = self.co_varnames.index(varname)
            except ValueError:
                arg = len(self.co_varnames)
                self.co_varnames.append(varname)
            self.emit_arg(op, arg)
        setattr(Code, opname[op], with_name(do_local, opname[op]))

for op in hasjrel + hasjabs:
    if not hasattr(Code, opname[op]):
        def do_jump(self, address=None, op=op):
            self.stackchange(stack_effects[op][0], stack_effects[op][1])
            return self.jump(op, address)
        setattr(Code, opname[op], with_name(do_jump, opname[op]))


def gen_map(code, ob):
    code.BUILD_MAP(0)
    for k, v in ob.items():
        code.DUP_TOP()
        code(k, v)
        code.ROT_THREE()
        code.STORE_SUBSCR()


def gen_tuple(code, ob):
    code(*ob)
    return code.BUILD_TUPLE(len(ob))


def gen_list(code, ob):
    code(*ob)
    return code.BUILD_LIST(len(ob))

generate_types = {
    int: Code.LOAD_CONST,
    long: Code.LOAD_CONST,
    bool: Code.LOAD_CONST,
    CodeType: Code.LOAD_CONST,
    str: Code.LOAD_CONST,
    unicode: Code.LOAD_CONST,
    complex: Code.LOAD_CONST,
    float: Code.LOAD_CONST,
    type(None): Code.LOAD_CONST,
    tuple: gen_tuple,
    list: gen_list,
    dict: gen_map,
}


class _se(object):
    """Quick way of defining static stack effects of opcodes"""
    POP_TOP = END_FINALLY = POP_JUMP_IF_FALSE = POP_JUMP_IF_TRUE = 1, 0
    ROT_TWO = 2, 2
    ROT_THREE = 3, 3
    ROT_FOUR = 4, 4
    DUP_TOP = 1, 2
    UNARY_POSITIVE = UNARY_NEGATIVE = UNARY_NOT = UNARY_CONVERT = \
        UNARY_INVERT = GET_ITER = LOAD_ATTR = IMPORT_FROM = 1, 1

    BINARY_POWER = BINARY_MULTIPLY = BINARY_DIVIDE = BINARY_FLOOR_DIVIDE = \
        BINARY_TRUE_DIVIDE = BINARY_MODULO = BINARY_ADD = BINARY_SUBTRACT = \
        BINARY_SUBSCR = BINARY_LSHIFT = BINARY_RSHIFT = BINARY_AND = \
        BINARY_XOR = BINARY_OR = COMPARE_OP = 2, 1

    INPLACE_POWER = INPLACE_MULTIPLY = INPLACE_DIVIDE = \
        INPLACE_FLOOR_DIVIDE = INPLACE_TRUE_DIVIDE = INPLACE_MODULO = \
        INPLACE_ADD = INPLACE_SUBTRACT = INPLACE_LSHIFT = INPLACE_RSHIFT = \
        INPLACE_AND = INPLACE_XOR = INPLACE_OR = 2, 1

    SLICE_0, SLICE_1, SLICE_2, SLICE_3 = \
        (1, 1), (2, 1), (2, 1), (3, 1)
    STORE_SLICE_0, STORE_SLICE_1, STORE_SLICE_2, STORE_SLICE_3 = \
        (2, 0), (3, 0), (3, 0), (4, 0)
    DELETE_SLICE_0, DELETE_SLICE_1, DELETE_SLICE_2, DELETE_SLICE_3 = \
        (1, 0), (2, 0), (2, 0), (3, 0)

    STORE_SUBSCR = 3, 0
    DELETE_SUBSCR = STORE_ATTR = 2, 0
    DELETE_ATTR = STORE_DEREF = 1, 0
    PRINT_EXPR = PRINT_ITEM = PRINT_NEWLINE_TO = IMPORT_STAR = 1, 0
    RETURN_VALUE = YIELD_VALUE = STORE_NAME = STORE_GLOBAL = STORE_FAST = 1, 0
    PRINT_ITEM_TO = LIST_APPEND = 2, 0

    LOAD_LOCALS = LOAD_CONST = LOAD_NAME = LOAD_GLOBAL = LOAD_FAST = \
        LOAD_CLOSURE = LOAD_DEREF = IMPORT_NAME = BUILD_MAP = 0, 1

    EXEC_STMT = BUILD_CLASS = 3, 0
    JUMP_IF_TRUE = JUMP_IF_FALSE = \
        JUMP_IF_TRUE_OR_POP = JUMP_IF_FALSE_OR_POP = 1, 1


if sys.version >= "2.5":
    _se.YIELD_VALUE = 1, 1

stack_effects = [(0, 0)] * 256

for opcode_name in opcode:
    op = opcode[opcode_name]
    opcode_name = opcode_name.replace('+', '_')

    if hasattr(_se, opcode_name):
        # update stack effects table from the _se class
        stack_effects[op] = getattr(_se, opcode_name)

    if not hasattr(Code, opcode_name):
        # Create default method for Code class
        if op >= HAVE_ARGUMENT:
            def do_op(self, arg, op=op, se=stack_effects[op]):
                self.stackchange(se[0], se[1])
                self.emit_arg(op, arg)
        else:
            def do_op(self, op=op, se=stack_effects[op]):
                self.stackchange(se[0], se[1])
                self.emit(op)

        setattr(Code, opcode_name, with_name(do_op, opcode_name))
