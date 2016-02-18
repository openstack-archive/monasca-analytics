#!/usr/bin/env python

"""DSL Error classes."""

import abc


class DSLException(Exception):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __str__(self):
        pass


class DSLExistingConnection(DSLException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        DSLException.__str__(self)
        return repr(self._value)


class DSLInexistentComponent(DSLException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        DSLException.__str__(self)
        return repr(self._value)


class DSLInvalidConnection(DSLException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        DSLException.__str__(self)
        return repr(self._value)


class DSLInterpreterException(DSLException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        DSLException.__str__(self)
        return repr(self._value)
