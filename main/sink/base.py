#!/usr/bin/env python

import abc

from main.component import base


class BaseSink(base.BaseComponent):
    """Base class for dstream sink to be extended by concrete dstream sinks."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def sink_dstream(self, dstream):
        pass

    @abc.abstractmethod
    def sink_ml(self, voter_id, matrix):
        pass
