from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import IsolationForest


def create_pipeline(contamination: float = 0.05) -> Pipeline:
    """
    Numeric-only pipeline (categoricals are already encoded upstream
    in feature_engineering.prepare_features).
    """
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("detector", IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=200,
        )),
    ])
