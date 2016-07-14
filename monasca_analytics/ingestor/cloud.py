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

import json
import logging

import numpy as np
import voluptuous

from monasca_analytics.ingestor import base
import monasca_analytics.util.spark_func as fn
from monasca_analytics.util import validation_utils as vu

logger = logging.getLogger(__name__)


class CloudIngestor(base.BaseIngestor):
    """Data ingestor for Cloud"""

    def __init__(self, _id, _config):
        super(CloudIngestor, self).__init__(_id=_id, _config=_config)

    @staticmethod
    def validate_config(_config):
        cloud_schema = voluptuous.Schema({
            "module": voluptuous.And(basestring, vu.NoSpaceCharacter())
        }, required=True)
        return cloud_schema(_config)

    @staticmethod
    def get_params():
        return []

    def map_dstream(self, dstream):
        features_list = list(self._features)
        return dstream.map(fn.from_json)\
            .map(lambda rdd_entry: CloudIngestor._process_data(
                rdd_entry,
                features_list))

    @staticmethod
    def get_default_config():
        return {"module": CloudIngestor.__name__}

    # TODO(David): With the new model, this can now be method, and the lambda
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
