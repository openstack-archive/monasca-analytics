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

import logging

import six
import voluptuous

import monasca_analytics.ingestor.iptables as ip_ing
import monasca_analytics.ldp.base as bt
from monasca_analytics.sml import svm_one_class
import monasca_analytics.util.spark_func as fn
from monasca_analytics.util import validation_utils as vu

logger = logging.getLogger(__name__)

FEATURES = "features"
MATRIX = "matrix"


class IptablesLDP(bt.BaseLDP):
    """An anomaly detection life module"""

    @staticmethod
    def validate_config(_config):
        iptables_ldp_schema = voluptuous.Schema({
            "module": voluptuous.And(six.string_types[0],
                                     vu.NoSpaceCharacter())
        }, required=True)
        return iptables_ldp_schema(_config)

    @staticmethod
    def get_default_config():
        return {"module": IptablesLDP.__name__}

    @staticmethod
    def get_params():
        return []

    def map_dstream(self, dstream):
        """Detect anomalies in a dstream using the learned classifier

        :type dstream: pyspark.streaming.DStream
        :param dstream: Spark's DStream
        """
        data = self._data
        return dstream.map(fn.from_json)\
            .map(lambda x: (x['ctime'], x))\
            .groupByKey()\
            .flatMap(lambda r: IptablesLDP._detect_anomalies(r[1], data))

    @staticmethod
    def _detect_anomalies(rdd_entry, data):
        """Classifies and marks the RDD entry as anomalous or non-anomalous

        :type rdd_entry: list[dict]
        :param rdd_entry: entry to be classified
        :type data: dict
        :param data: contains the features and the classifier
        """
        new_entries = []
        events = []
        ctimes = []
        for event in rdd_entry:
            events.append(event[ip_ing.RDD_EVENT])
            ctimes.append(event["ctime"])
        features = data[FEATURES]
        classifier = data[MATRIX]

        if features is None or classifier is None:
            return events

        X = ip_ing.IptablesIngestor.vectorize_events(events, features)
        Y = classifier.predict(X)
        for i in range(len(events)):
            event = events[i]
            event["ctime"] = ctimes[i]
            if Y[0] == svm_one_class.ANOMALY:
                event["anomalous"] = True
            else:
                event["anomalous"] = False
            new_entries.append(event)
        return new_entries
