from main.source import base


class MockBaseSource(base.BaseSource):

    validation_cnt = 0

    def __init__(self, _id, _config):
        MockBaseSource.validation_cnt = 0
        self.before_binding_cnt = 0
        self.after_binding_cnt = 0
        self.before_unbinding_cnt = 0
        self.after_unbinding_cnt = 0
        super(MockBaseSource, self).__init__(_id, _config)

    @staticmethod
    def validate_config(_config):
        MockBaseSource.validation_cnt += 1

    @staticmethod
    def get_default_config():
        {"module": MockBaseSource.__name__}

    def create_dstream(self, ssc):
        self.before_binding_cnt += 1
        return None

    def terminate_source(self):
        pass

    def get_feature_list(self):
        pass
