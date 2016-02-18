import numpy as np

from main.sml import svm_one_class as svm


class MockClassifier():

    def __init__(self, predict_anomaly=False):
        self._predict_anomaly = predict_anomaly
        self.predict_cnt = 0

    def predict(self, _):
        self.predict_cnt += 1
        if self._predict_anomaly:
            return np.array([svm.ANOMALY])
        return np.array([svm.NON_ANOMALY])
