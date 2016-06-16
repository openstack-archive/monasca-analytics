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

import time


class MockSparkContext(object):

    def __init__(self, appName):
        self.parallelize_cnt = 0
        pass

    def parallelize(self, param):
        self.parallelize_cnt += 1
        pass


class MockStreamingContext(object):

    def __init__(self, sc, streaming_batch_interval):
        self.sparkContext = sc
        self.started_cnt = 0
        self.stopped_cnt = 0
        self._textFileStreamDirectory = None
        self._port = None

    def start(self):
        self.started_cnt += 1

    def stop(self, stopSparkContext=True, stopGraceFully=False):
        self.stopped_cnt += 1

    def awaitTermination(self):
        self.stopped_cnt += 1

    def textFileStream(self, directory):
        self._textFileStreamDirectory = directory
        return "file_dstream"

    def socketTextStream(self, host, port):
        self._port = port
        self._host = host
        return MockDStream(None, None, None)

    def mockDStream(self):
        return MockDStream(None, None, None)


class MockKafkaUtils(object):

    @staticmethod
    def createStream(ssc, hostport, groupid, topics):
        return "kafka_dstream"


class MockDStream(object):

    def __init__(self, jdstream, ssc, jrdd_deserializer):
        self.transform_cnt = 0
        self.join_cnt = 0
        self.foreachRDD_cnt = 0
        self.map_cnt = 0
        self.jdstream = jdstream
        self.ssc = ssc
        self.fake_rdd = None
        self.jrdd_deserializer = jrdd_deserializer

    def transform(self, func):
        self.transform_cnt += 1
        self.fake_rdd = MockRDD(
            self.jdstream, self.ssc, self.jrdd_deserializer)
        timestamp = time.time()
        func(timestamp, self.fake_rdd)

    def join(self, other_dstream):
        self.join_cnt += 1

    def foreachRDD(self, func):
        self.foreachRDD_cnt += 1
        self.fake_rdd = MockRDD(
            self.jdstream, self.ssc, self.jrdd_deserializer)
        timestamp = time.time()
        func(timestamp, self.fake_rdd)

    def map(self, func):
        self.map_cnt += 1
        self.fake_rdd = MockRDD(
            self.jdstream, self.ssc, self.jrdd_deserializer)
        for rdd_entry in self.fake_rdd.collect():
            func(rdd_entry)

    def pprint(self, num=10):
        pass


class MockRDD(object):

    def __init__(self, jdstream, ssc, jrdd_deserializer):
        self.collect_cnt = 0
        self._rdd_entries = []

    def set_rdd_entries(self, rdd_entries):
        self._rdd_entries = rdd_entries

    def collect(self):
        self.collect_cnt += 1
        return self._rdd_entries
