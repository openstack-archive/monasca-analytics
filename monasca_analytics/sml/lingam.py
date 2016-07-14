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
import math

import numpy as np
from sklearn import decomposition
import voluptuous

import monasca_analytics.banana.typeck.type_util as type_util
import monasca_analytics.component.params as params

from monasca_analytics.sml import base
from monasca_analytics.util import validation_utils as vu

logger = logging.getLogger(__name__)


class LiNGAM(base.BaseSML):
    """Causality discovery assuming a linear non gaussian acyclic data model"""

    def __init__(self, _id, _config):
        super(LiNGAM, self).__init__(_id, _config)
        self._threshold = _config["threshold"]
        self._threshold = 0.1

    @staticmethod
    def validate_config(_config):
        lingam_schema = voluptuous.Schema({
            "module": voluptuous.And(basestring, vu.NoSpaceCharacter()),
            "threshold": float
        }, required=True)
        return lingam_schema(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": LiNGAM.__name__,
            "threshold": 0.1
        }

    @staticmethod
    def get_params():
        return [
            params.ParamDescriptor('threshold', type_util.Number(), 0.1)
        ]

    def number_of_samples_required(self):
        return 5000

    def learn_structure(self, samples):
        logger.debug(samples.shape)
        logger.debug(samples)
        threshold = self._threshold
        causality_matrix, _ = LiNGAM._discover_structure(samples)
        structure = causality_matrix > threshold

        logger.info("Causality Matrix: {0}".format(causality_matrix))
        logger.info("Learned causality: {0}".format(structure))
        return structure

    @staticmethod
    def _discover_structure(data):

        # Add a random noise uniformly distributed to avoid singularity
        # when performing the ICA
        data += np.random.random_sample(data.shape)

        # Create the ICA node to get the inverse of the mixing matrix
        k, w, _ = decomposition.fastica(data)

        w = np.dot(w, k)
        n = w.shape[0]
        best_nzd = float("inf")
        best_slt = float("inf")
        best_w_permuted = w
        causality_matrix = None
        causal_perm = None

        if n < 9:
            perm = LiNGAM._perms(n)

            for i in range(perm.shape[1]):
                perm_matrix = np.eye(n)
                perm_matrix = perm_matrix[:, perm[:, i]]
                w_permuted = perm_matrix.dot(w)
                cost = LiNGAM._cost_non_zero_diag(w_permuted)
                if cost < best_nzd:
                    best_nzd = cost
                    best_w_permuted = w_permuted

            w_opt = best_w_permuted

            w_opt = w_opt / np.diag(w_opt).reshape((n, 1))
            b_matrix = np.eye(n) - w_opt
            best_b_permuted = b_matrix
            best_i = 0

            for i in range(perm.shape[1]):
                b_permuted = b_matrix[:, perm[:, i]][perm[:, i], :]
                cost = LiNGAM._cost_strictly_lower_triangular(
                    b_permuted)
                if cost < best_slt:
                    best_slt = cost
                    best_i = i
                    best_b_permuted = b_permuted

            causal_perm = perm[:, best_i]
            causality_matrix = b_matrix

            percent_upper = best_slt / np.sum(best_b_permuted ** 2)

            if percent_upper > 0.2:
                # TODO(David): Change that code to raise an exception instead
                logger.error("LiNGAM failed to run on the data set")
                logger.error(
                    "--> B permuted matrix is at best {}% lower triangular"
                    .format(percent_upper))

        return causality_matrix, causal_perm

    @staticmethod
    def _cost_strictly_lower_triangular(b):
        return np.sum((np.tril(b, -1) - b) ** 2)

    @staticmethod
    def _cost_non_zero_diag(w):
        return np.sum(1 / np.abs(np.diag(w)))

    @staticmethod
    def _perms(n):
        k = 1
        p = np.empty((2 * n - 1, math.factorial(n)), np.uint8)
        for i in range(n):
            p[i, :k] = i
            p[i + 1:2 * i + 1, :k] = p[:i, :k]
            for j in range(i):
                p[:i + 1, k * (j + 1):k * (j + 2)] = p[j + 1:j + i + 2, :k]
            k *= i + 1
        return p[:n, :]
