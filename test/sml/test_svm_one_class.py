#!/usr/bin/env python

import logging
import unittest

import numpy as np
from sklearn import svm

from main.sml import svm_one_class

logger = logging.getLogger(__name__)


class TestSvmOneClass(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.svm = svm_one_class.SvmOneClass("fakeid", {"module": "fake"})

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def get_testing_data(self):
        a = np.random.uniform(size=1000)
        b = np.random.uniform(size=1000)
        c = np.random.uniform(size=1000)
        d = np.random.uniform(size=1000)
        return np.array([a, b, c, d]).T

    def test_generate_train_test_sets(self):
        data = self.get_testing_data()
        train, test = self.svm._generate_train_test_sets(data, 0.6)
        self.assertEqual(600, len(train))
        self.assertEqual(400, len(test))

    def test_learn_structure(self):
        data = self.get_testing_data()
        clf = self.svm.learn_structure(data)
        self.assertTrue(isinstance(clf, svm.OneClassSVM))

if __name__ == "__main__":
    unittest.main()
