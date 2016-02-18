#!/usr/bin/env python

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
