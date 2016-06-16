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

import abc
import logging
import six

import numpy as np

logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Aggregator(object):
    """Aggregator that accumulates data and sends it to SMLs"""

    def __init__(self, driver):
        """BaseAggregator constructor.

        :type driver: monasca_analytics.spark.driver.DriverExecutor
        :param driver: The driver that manages spark
        """
        self._combined_stream = None
        self._smls = []
        self._samples = None
        self._driver = driver

    def append_sml(self, l):
        """The given sml will now be owned and receive the accumulated data

        :type l: monasca_analytics.sml.base.BaseSML
        :param l: The sml to connect to.
        """
        self._smls.append(l)

    def accumulate_dstream_samples(self, stream):
        """Accumulate the samples coming from a stream

        The first time this function is called it sets the _combined_stream
        to be the _stream parameter, and the _output_stream to be the
        transformed version (according to the logic implemented by children
        of this class) of the _combined_stream.
        The consecutive times, it joins the _stream to the aggregated stream,
        so at runtime _combined_stream is a funnel of all streams passed
        to this function.

        :type stream: pyspark.streaming.DStream
        :param stream: stream to be collected
        """
        if self._combined_stream is None:
            self._combined_stream = stream
        else:
            self._combined_stream = self._combined_stream.union(stream)

    def prepare_final_accumulate_stream_step(self):
        """Accumulate each sample into an ndarray.

        This can only be called once accumulate_dstream_samples has been
        called on every stream that need to be accumulated together.
        """
        if self._combined_stream is not None:
            self._combined_stream.foreachRDD(
                lambda _, rdd: self._processRDD(rdd))

    def _processRDD(self, rdd):
        """Process the RDD

        :type rdd: pyspark.RDD
        :param rdd: A Spark Resilient Distributed Dataset
        """
        if len(self._smls) > 0:
            rdd_entries = rdd.collect()
            for rdd_entry in rdd_entries:
                if self._samples is not None:
                    self._samples = np.vstack([self._samples, rdd_entry])
                else:
                    self._samples = rdd_entry
            self._check_smls()
        else:
            self._samples = None

    def _check_smls(self):
        """Detect if a SML is ready to learn from the set.

        If it is, for simplicity we remove it from the list of SMLs.
        """
        if self._samples is None:
            return

        def has_learn(sml, samples):
            nb_samples = samples.shape[0]
            tst = sml.number_of_samples_required() <= nb_samples
            if tst:
                sml.learn(samples)
            return not tst

        logger.debug(self._samples.shape)
        self._smls[:] = [l for l in self._smls if has_learn(l, self._samples)]
        if len(self._smls) == 0:
            self._driver.move_to_phase2()
