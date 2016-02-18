#!/usr/bin/env python

import unittest
# This file is name kafkas otherwise it will conflict
# with the global import 'kafka'
import main.sink.kafkas as kf


class KafkaSinkTest(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

        class MockedKafka(object):
            def __init__(self):
                self.has_been_called = False

            def KafkaProducer(self, *_, **kwargs):
                self.has_been_called = True

        self.mock_kafka = MockedKafka()
        self.original_kafka = kf.kafka
        kf.kafka = self.mock_kafka

    def testKafkaSinkInit(self):
        kf.KafkaSink("id", {
            "module": "KafkaSink",
            "params": {
                "host": "localhost",
                "port": 00,
                "topic": "boom",
            }
        })
        self.assertTrue(self.mock_kafka)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        kf.kafka = self.original_kafka

    def test_get_default_config(self):
        default_config = kf.KafkaSink.get_default_config()
        kf.KafkaSink.validate_config(default_config)
        self.assertEqual("KafkaSink", default_config["module"])

if __name__ == "__main__":
    unittest.main()
