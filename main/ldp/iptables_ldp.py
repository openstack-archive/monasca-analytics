#!/usr/bin/env python

import json
import logging

import schema

from main.ingestor import iptables as ip_ing
import main.ldp.base as bt
from main.sml import svm_one_class

logger = logging.getLogger(__name__)

FEATURES = "features"
MATRIX = "matrix"


class IptablesLDP(bt.BaseLDP):
    """An anomaly detection life module"""

    @staticmethod
    def validate_config(_config):
        return schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
        }).validate(_config)

    @staticmethod
    def get_default_config():
        return {"module": IptablesLDP.__name__}

    def map_dstream(self, dstream):
        """Detect anomalies in a dstream using the learned classifier

        :param dstream: pyspark.streaming.DStream
        """
        data = self._data
        return dstream.flatMap(lambda r:
                               self._detect_anomalies(r, data))

    def _detect_anomalies(self, rdd_entry, data):
        """Classifies and marks the RDD entry as anomalous or non-anomalous

        :param rdd_entry: pyspark.streaming.RDD -- entry to be classified
        :param data: dict -- contains the features and the classifier
        """
        rdd_entry = json.loads(rdd_entry)
        new_entries = []
        events = rdd_entry[ip_ing.RDD_EVENTS]
        features = data[FEATURES]
        classifier = data[MATRIX]

        if features is None or classifier is None:
            return events

        X = ip_ing.IptablesIngestor._vectorize_events(events, features)
        Y = classifier.predict(X)
        for i in range(len(events)):
            event = events[i]
            event["ctime"] = rdd_entry["ctime"]
            if Y[0] == svm_one_class.ANOMALY:
                event["anomalous"] = True
            else:
                event["anomalous"] = False
            new_entries.append(event)
        return new_entries
