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
import logging

from monasca_analytics.component import base

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

        :rtype: list[str]
        """
        pass

    @abc.abstractmethod
    def create_dstream(self, ssc):
        """Create a dstream to be consumed by Monanas.

        :type ssc: pyspark.streaming.StreamingContext
        :param ssc: Spark streaming context. It shouldn't be stored by self.
        :rtype: pyspark.streaming.DStream
        :returns: a Spark dstream to be consumed by Monanas.
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
