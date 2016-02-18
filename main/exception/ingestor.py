#!/usr/bin/env python

"""Data Ingestor Error classes."""

import abc


class IngestorException(Exception):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __str__(self):
        pass


class IngestorNoSuchSourceModel(IngestorException):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        IngestorException.__str__(self)
        return repr(self._value)
