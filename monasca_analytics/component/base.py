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


class abstractstatic(staticmethod):
    """
    See http://stackoverflow.com/a/4474495 for
    more details on this class purpose
    """
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

        :type _id: str
        :param _id: identifier of this Source
        :type _config: dict
        :param _config: configuration of this Source
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

        :type _config: dict
        :param _config: configuration of this module to be validated.
        """
        pass

    @abstractstatic
    def get_default_config():  # @NoSelf
        """Abstract static method that returns the default configuration.

        To be implemented by BaseComponent children. It has to return a default
        valid configuration for the module.

        :rtype: dict
        :returns: default configuration
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
