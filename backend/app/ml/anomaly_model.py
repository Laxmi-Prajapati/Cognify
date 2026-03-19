import pandas as pd
import numpy as np
from app.ml.model_pipeline import create_pipeline
from app.config import settings


class AnomalyModel:
    """
    Wraps IsolationForest pipeline.
    Returns anomaly flag (-1/1) AND a normalized anomaly score [0,1].
    """

    def __init__(self):
        self.pipeline = create_pipeline(settings.ISOLATION_FOREST_CONTAMINATION)
        self.trained = False

    def train(self, X: pd.DataFrame):
        self.pipeline.fit(X)
        self.trained = True

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.trained:
            self.train(X)

        preds = self.pipeline.predict(X)                          # 1 = normal, -1 = anomaly
        scores = self.pipeline.decision_function(X)               # higher = more normal

        # Normalize scores to [0, 1] — higher means MORE anomalous
        min_s, max_s = scores.min(), scores.max()
        if max_s != min_s:
            normalized = 1 - (scores - min_s) / (max_s - min_s)
        else:
            normalized = np.zeros(len(scores))

        result = X.copy()
        result["ml_anomaly_flag"] = (preds == -1).astype(int)
        result["ml_anomaly_score"] = np.round(normalized, 4)
        return result
