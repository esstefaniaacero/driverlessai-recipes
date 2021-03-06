"""Recall: `TP / (TP + FN)`. Binary uses threshold of 0.5 (please adjust), multiclass uses argmax to assign labels."""
import typing
import numpy as np
from h2oaicore.metrics import CustomScorer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import recall_score


class recall(CustomScorer):
    _description = "Recall: `tp / (tp + fn)`"
    _binary = True
    _multiclass = True
    _maximize = True
    _perfect_score = 1
    _display_name = "Recall"
    _threshold = 0.5  # Example only, should be adjusted based on domain knowledge and other experiments

    def score(self,
              actual: np.array,
              predicted: np.array,
              sample_weight: typing.Optional[np.array] = None,
              labels: typing.Optional[np.array] = None) -> float:
        lb = LabelEncoder()
        labels = lb.fit_transform(labels)
        actual = lb.transform(actual)
        method = "binary"
        if len(labels) > 2:
            predicted = np.argmax(predicted, axis=1)
            method = "micro"
        else:
            predicted = (predicted > self._threshold)

        return recall_score(actual, predicted, labels=labels, average=method, sample_weight=sample_weight)
