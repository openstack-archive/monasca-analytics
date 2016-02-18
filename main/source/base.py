#!/usr/bin/env python

import abc
import logging

from main.component import base

logger = logging.getLogger(__name__)


class BaseSource(base.BaseComponent):
    """Base class for source provider

    To be extended by concrete sources
    """

    def __init__(self, _id, _config):
        super(BaseSource, self).__init__(_id, _config)
        # This is fine to store the config within the class for sources
        # as they're not supposed to do any processing with the dstream
        # Thus won't be transmitted to workers.
        self._config = _config

    @abc.abstractmethod
    def get_feature_list(self):
        """Returns the list of features names.

        :returns: list[str]
        """
        pass

    @abc.abstractmethod
    def create_dstream(self, ssc):
        """Create a dstream to be consumed by Monanas.

        :param ssc: pyspark.streaming.StreamingContext -- Spark streaming
        context. It shouldn't be stored by the source.
        :returns: pyspark.streaming.DStream -- a Spark dstream to be
        consumed by Monanas.
        """
        pass

    @abc.abstractmethod
    def terminate_source(self):
        """Terminate the source.

        Note to implementers:

            Please, implement the termination logic here, like
            disconnecting from a server, unsubscribing from a queue,
            closing a file, etc.
        """
        pass
