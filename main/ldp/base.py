#!/usr/bin/env python

import abc

from main.component import base


class BaseLDP(base.BaseComponent):
    """Base class for Live Data Processor (LDP), to be extended"""

    __metaclass__ = abc.ABCMeta

    def __init__(self, _id, _config):
        """Constructor with ID and configuration

        :param _id: str -- ID assigned to this component
        :param _config: dict -- configuration of this component
        """
        super(BaseLDP, self).__init__(_id, _config)
        self._features = None
        self._data = {
            "features": None,
            "matrix": None
        }

    @abc.abstractmethod
    def map_dstream(self, dstream):
        pass

    def set_voter_output(self, matrix):
        """Assign the features and matrix to the _data object that

        :param features: list[str]
        :param matrix: numpy.ndarray
        """
        self._data["features"] = self._features
        self._data["matrix"] = matrix

    def set_feature_list(self, features):
        """Set the list of features

        :param features: list[str]
        """
        self._features = features
