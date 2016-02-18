import logging

import schema

from main.voter import base

logger = logging.getLogger(__name__)


class PickIndexVoter(base.BaseVoter):

    def __init__(self, _id, _config):
        super(PickIndexVoter, self).__init__(_id, _config)
        self._index = _config["params"]["index"]
        self._index = 0

    @staticmethod
    def validate_config(_config):
        schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
            "params": {
                "index": schema.And(int, lambda i: i >= 0)
            }
        }).validate(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": PickIndexVoter.__name__,
            "params": {
                "index": 0
            }
        }

    def elect_structure(self, structures):
        return structures[
            min(len(structures) - 1,
                self._index)]
