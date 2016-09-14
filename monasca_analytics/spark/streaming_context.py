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

import os.path as os_path
import pyspark.sql as sql
import pyspark.streaming as streaming

logger = logging.getLogger(__name__)


class DriverStreamingListener(streaming.StreamingListener):

    @staticmethod
    def onBatchCompleted(batchCompleted):
        logger.debug("Batch Completed: \n\t{}\n".format(
            batchCompleted))

    @staticmethod
    def onBatchStarted(batchStarted):
        logger.debug("Batch Started: \n\t{}\n".format(
            batchStarted))

    @staticmethod
    def onBatchSubmitted(batchSubmitted):
        logger.debug("Batch submitted: \n\t{}\n".format(
            batchSubmitted))

    @staticmethod
    def onOutputOperationCompleted(outputOperationCompleted):
        logger.debug("Job of batch has completed: \n\t{}\n".format(
            outputOperationCompleted))

    @staticmethod
    def onOutputOperationStarted(outputOperationStarted):
        logger.debug("Job of a batch has started: \n\t{}\n".format(
            outputOperationStarted))

    @staticmethod
    def onReceiverError(receiverError):
        logger.warn("Receiver has reported an error: \n\t{}\n".format(
            receiverError))

    @staticmethod
    def onReceiverStarted(receiverStarted):
        logger.debug("Receiver has been started: \n\t{}\n".format(
            receiverStarted))

    @staticmethod
    def onReceiverStopped(receiverStopped):
        logger.debug("Receiver has stopped: \n\t{}\n".format(
            receiverStopped))


def create_streaming_context(spark_context, config):
    """
    Create a streaming context with a custom Streaming Listener
    that will log every event.
    :param spark_context: Spark context
    :type spark_context: pyspark.SparkContext
    :param config: dict
    :return: Returns a new streaming context from the given context.
    :rtype: pyspark.streaming.StreamingContext
    """
    ssc = streaming.StreamingContext(spark_context, config[
        "spark_config"]["streaming"]["batch_interval"])
    ssc.addStreamingListener(DriverStreamingListener)
    directory = os_path.expanduser("~/checkpointing")
    logger.info("Checkpointing to `{}`".format(directory))
    # Commented out to fix a crash occurring when
    # phase 1 is used. The reason of the crash is still unclear
    # but Spark complains about the SSC being transferred
    # to workers.
    # ssc.checkpoint(directory)
    return ssc


def get_sqlcontext_instance(spark_context):
    """
    :type spark_context: pyspark.SparkContext
    :param spark_context: The currently active Spark Context
    :return: Returns the SQLContext
    :rtype: sql.SQLContext
    """
    if 'sqlContextSingletonInstance' not in globals():
        globals()['sqlContextSingletonInstance'] = sql.SQLContext(
            spark_context)
    return globals()['sqlContextSingletonInstance']
