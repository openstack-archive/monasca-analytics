from main.ingestor import base


class IngestorBasicChild(base.BaseIngestor):
    """
    BaseIngestor with abstract classes implemented in order to test it
    """

    validation_cnt = 0

    def __init__(self, _id, _config):
        IngestorBasicChild.validation_cnt = 0
        self.process_stream_cnt = 0
        self.before_stop_ingesting_cnt = 0
        super(IngestorBasicChild, self).__init__(_id, _config)

    @staticmethod
    def validate_config(_config):
        IngestorBasicChild.validation_cnt += 1

    @staticmethod
    def get_default_config():
        {"module": IngestorBasicChild.__name__}

    def map_dstream(self):
        self.process_stream_cnt += 1

    def before_stop_ingesting(self):
        self.before_stop_ingesting_cnt += 1


class MockIngestor(IngestorBasicChild):
    """
    Mock of BaseIngestor in order to test code that uses it
    """

    def __init__(self, _id, _config):
        self.ingest_cnt = 0
        super(MockIngestor, self).__init__(_id, _config)

    def ingest(self, dstream, ssc):
        self.ingest_cnt += 1
