import time


class MockSparkContext():

    def __init__(self, appName):
        self.parallelize_cnt = 0
        pass

    def parallelize(self, param):
        self.parallelize_cnt += 1
        pass


class MockStreamingContext():

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


class MockKafkaUtils():

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
