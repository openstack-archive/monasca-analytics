#!/usr/bin/env python

# Copyright (c) 2016 Hewlett Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import monasca_analytics.config.const as conf_const
import monasca_analytics.ingestor.base as ingestor
import monasca_analytics.ldp.base as ldp
import monasca_analytics.sink.base as sink
import monasca_analytics.sml.base as sml
import monasca_analytics.source.base as source
import monasca_analytics.voter.base as voter


import six


def into_old_conf_dict(components):
    """
    Convert the provided dict of components
    keyed by ids into a dict keyed by component
    type. This is the data structure used to do
    the validation of JSON configuration (the old format).

    :type components: dict[str, object]
    :param components: The dictionary of components.
    :return: Returns the old conf dictionary.
    """
    return {
        conf_const.INGESTORS:
            dict(filter(lambda x: isinstance(x[1], ingestor.BaseIngestor),
                        six.iteritems(components))),
        conf_const.VOTERS:
            dict(filter(lambda x: isinstance(x[1], voter.BaseVoter),
                        six.iteritems(components))),
        conf_const.SINKS:
            dict(filter(lambda x: isinstance(x[1], sink.BaseSink),
                        six.iteritems(components))),
        conf_const.LDPS:
            dict(filter(lambda x: isinstance(x[1], ldp.BaseLDP),
                        six.iteritems(components))),
        conf_const.SOURCES:
            dict(filter(lambda x: isinstance(x[1], source.BaseSource),
                        six.iteritems(components))),
        conf_const.SMLS:
            dict(filter(lambda x: isinstance(x[1], sml.BaseSML),
                        six.iteritems(components))),
    }
