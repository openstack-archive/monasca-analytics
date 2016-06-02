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

import json
import logging

import numpy as np
import schema

from monasca_analytics.ingestor import base
from monasca_analytics.source import iptables_markov_chain as src

logger = logging.getLogger(__name__)

RDD_EVENTS = "events"
RDD_CTIME = "ctime"
EVENT_MSG = "msg"


class IptablesIngestor(base.BaseIngestor):
    """This ingestor class implements an IPTable parsing and vectorization.

    Assuming the dstream contains iptables that have been triggered, it creates
    an np array for each sample wit the number of times that each IPTable has
    been triggered.
    """

    def __init__(self, _id, _config):
        super(IptablesIngestor, self).__init__(_id=_id, _config=_config)

    @staticmethod
    def validate_config(_config):
        return schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i))
        }).validate(_config)

    @staticmethod
    def get_default_config():
        return {"module": IptablesIngestor.__name__}

    def map_dstream(self, dstream):
        new_dstream = dstream.map(
            lambda rdd_entry: IptablesIngestor._process_data(rdd_entry,
                                                             self._features))
        return new_dstream

    @staticmethod
    def _process_data(rdd_entry, feature_list):
        """Parse and vectorize the rdd_entry

        Assuming the rdd_entry is encoded in JSON format, this method
        gets the events and vectorizes them according to the features.

        :type rdd_entry: str
        :param rdd_entry: json encoded in a string, containing
                          the data of an RDD
        :type feature_list: list[str]
        :param feature_list: features to extract, in order
        """
        rdd_json = json.loads(rdd_entry)
        events = rdd_json[RDD_EVENTS]
        return IptablesIngestor._vectorize_events(events, feature_list)

    @staticmethod
    def _vectorize_events(events, feature_list):
        """Event vectorizing logic.

        For each event, we get the message,
        which is the IPTable that has been triggered.
        Then we get the corresponding feature for the IPtable.
        Finally, we increase the index of the vector corresponding to
        that feature.

        :type feature_list: list[str]
        :param feature_list: features to extract, in order
        """
        ret = np.zeros(len(feature_list))
        for event in events:
            iptable_id = src.iptables[event[EVENT_MSG]]
            feature = src.get_iptable_type(iptable_id)
            index = feature_list.index(feature)
            ret[index] += 1
        return ret
