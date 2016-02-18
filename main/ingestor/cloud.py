#!/usr/bin/env python

import json
import logging

import numpy as np
import schema

from main.ingestor import base

logger = logging.getLogger(__name__)


class CloudIngestor(base.BaseIngestor):
    """Data ingestor for Cloud"""

    def __init__(self, _id, _config):
        super(CloudIngestor, self).__init__(_id=_id, _config=_config)

    @staticmethod
    def validate_config(_config):
        return schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i))
        }).validate(_config)

    def map_dstream(self, dstream):
        feature_list = list(self._features)
        return dstream.map(
            lambda rdd_entry: CloudIngestor._process_data(rdd_entry,
                                                          feature_list))

    @staticmethod
    def get_default_config():
        return {"module": CloudIngestor.__name__}

    # TODO: With the new model, this can now be method, and the lambda
    #       can be removed.
    @staticmethod
    def _process_data(rdd_entry, feature_list):
        json_value = json.loads(rdd_entry)
        return CloudIngestor._parse_and_vectorize(json_value, feature_list)

    @staticmethod
    def _parse_and_vectorize(json_value, feature_list):
        values = {
            "support_1": 0
        }
        for feature in feature_list:
            values[feature] = 0
        for e in json_value["events"]:
            if e["id"] in values:
                values[e["id"]] += 1
        res = [values[f] for f in feature_list]
        return np.array(res)
