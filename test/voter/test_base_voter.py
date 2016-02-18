import unittest

from main.voter import base


class BaseVoterTest(unittest.TestCase):

    def setUp(self):
        self.vot = VoterBasicChild("fake_id", "fake_config")

    def tearDown(self):
        pass

    def test_suggest_structure_no_smls_or_structures(self):
        self.vot.suggest_structure("who", "struct")


class VoterBasicChild(base.BaseVoter):

    def __init__(self, _id, _config):
        self.elect_cnt = 0
        super(VoterBasicChild, self).__init__(_id, _config)

    def elect_structure(self, structures):
        self.elect_cnt += 1

    @staticmethod
    def validate_config(_config):
        pass

    @staticmethod
    def get_default_config():
        {"module": VoterBasicChild.__name__}
