#!/usr/bin/env python

import abc


class abstractstatic(staticmethod):

    __slots__ = ()

    def __init__(self, function):
        super(abstractstatic, self).__init__(function)
        function.__isabstractmethod__ = True
    __isabstractmethod__ = True


class BaseComponent(object):
    """Base class for all component types.

    Should be as lightweight as possible, becuase any data here will be sent
    to all workers every time a component is added.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, _id, _config):
        """BaseComponent constructor.

        :param _id: str -- identifier of this Source
        :param _config: dict -- configuration of this Source
        """
        self.validate_config(_config)
        self._id = _id

    @abstractstatic
    def validate_config(_config):  # @NoSelf
        """Abstract static method for configuration validation.

        To be implemented by BaseComponent children.
        It is called at creation time, and it should validate the
        schema of the configuration passed as parameter
        (i.e. check for expected keys and value format).
        This function should raise exceptions if the validation fails,
        otherwise it is assumed the validation was successful.

        :param _config: dict -- configuration of this module,
        to be validated.
        """
        pass

    @abstractstatic
    def get_default_config():  # @NoSelf
        """Abstract static method that returns the default configuration.

        To be implemented by BaseComponent children. It has to return a default
        valid configuration for the module.

        :returns: dict -- default configuration
        """
        pass

    def id(self):
        return self._id

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        return self._id == other.id()

    def __ne__(self, other):
        return not(self == other)

    def __str__(self):
        return self._id
