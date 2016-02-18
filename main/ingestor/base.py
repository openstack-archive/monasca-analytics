#!/usr/bin/env python

import abc
import logging

from main.component import base

logger = logging.getLogger(__name__)


class BaseIngestor(base.BaseComponent):
    """Base class for all the Ingestor modules"""

    def __init__(self, _id, _config):
        """Constructor with ID and configuration

        :param _id: str -- ID assigned to this component
        :param _config: dict -- configuration of this component
        """
        self._features = None
        super(BaseIngestor, self).__init__(_id, _config)

    @abc.abstractmethod
    def map_dstream(self, dstream):
        """Transforms the data provided by a dstream to another dstream

        Abstract method to be implemented by BaseIngestor children.
        The processed dstream should be returned.

        :param: dstream: pyspark.streaming.Dstream -- stream of data before
        being processed
        :returns: pyspark.streaming.Dstream: stream of data after
        being processed
        """
        pass

    def set_feature_list(self, features):
        """Set the list of features

        :param features: list[str]
        """
        self._features = features
