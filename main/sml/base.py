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


class BaseSML(base.BaseComponent):
    """Base SML, to be extended by statistical or machine learning classes"""

    def __init__(self, _id, _config):
        super(BaseSML, self).__init__(_id, _config)
        self._voter = None

    @abc.abstractmethod
    def learn_structure(self, samples):
        """Learn structure based on the provided data

        Abstract method to be implemented by subclasses.
        It should learn over those samples a structure such as
        a causality matrix or a decision tree that is then
        going to be suggested to a voter which then
        forward it to a LDP.

        :param samples: numpy.ndarray -- the list of samples to be processed
        :returns: numpy.ndarray
        """
        pass

    @abc.abstractmethod
    def number_of_samples_required(self):
        """This function returns the number of samples required

        :returns: int -- the number of samples required.
        """
        pass

    def learn(self, samples):
        """Learning phase

        This method is called by the aggregator owning this sml.

        :param samples: numpy.ndarray -- the list of samples that can be
        processed by the data.
        """
        self._voter.suggest_structure(self, self.learn_structure(samples))

    def set_voter(self, voter):
        if self._voter is not None:
            self._voter.remove_sml(self)
        self._voter = voter
        self._voter.append_sml(self)
