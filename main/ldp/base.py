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
