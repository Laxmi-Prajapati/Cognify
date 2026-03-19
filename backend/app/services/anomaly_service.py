import time
from collections import Counter
import pandas as pd
import numpy as np
from typing import Dict, Any
from collections import Counter

from app.data.data_cleaning import clean_sales_data
from app.data.feature_engineering import prepare_features
from app.ml.anomaly_model import AnomalyModel
from app.ml.severity_scorer import compute_severity
from app.audit.rule_engine import run_rule_engine
from app.rag.embedder import embed_anomalies
from app.rag.vector_store import vector_store

RAG_INDEX_LIMIT = 500
ML_BATCH_SIZE = 10_000


def run_full_audit(df_raw: pd.DataFrame) -> Dict[str, Any]:

    total_raw = len(df_raw)
    print(f"📥 Received {total_raw} rows")

    # --- Layer 1: Clean (all rows) ---
    t = time.time()
    df_clean = clean_sales_data(df_raw)
    print(f"✅ Cleaning done: {time.time()-t:.1f}s | {len(df_clean)} rows")

    # --- Layer 2: Rule-based (vectorized, all rows) ---
    t = time.time()
    df_with_rules = run_rule_engine(df_clean)
    print(f"✅ Rule engine done: {time.time()-t:.1f}s")

    # Debug: print rule violation breakdown
    all_rule_violations = []
    for v_list in df_with_rules["rule_violations"]:
        all_rule_violations.extend([v["policy_name"] for v in v_list])

    print("Rule breakdown:", Counter(all_rule_violations).most_common())

    # --- Layer 3: ML in batches (all rows) ---
    t = time.time()
    X = prepare_features(df_clean)
    ml_flags, ml_scores = _batch_ml_predict(X)
    df_with_rules["ml_anomaly_flag"] = ml_flags
    df_with_rules["ml_anomaly_score"] = ml_scores
    print(f"✅ ML done: {time.time()-t:.1f}s")

    # Debug: print rule violation breakdown
    print("ML only flagged:", (df_with_rules["ml_anomaly_flag"] == 1).sum())
    print("Rule only flagged:", (df_with_rules["rule_flag"] == 1).sum())
    print("Both flagged:", ((df_with_rules["ml_anomaly_flag"] == 1) & (df_with_rules["rule_flag"] == 1)).sum())

    # --- Combined flag ---
    df_with_rules["is_anomaly"] = (
        (df_with_rules["ml_anomaly_flag"] == 1) |
        (df_with_rules["rule_flag"] == 1)
    ).astype(int)

    # --- Severity scoring (vectorized) ---
    t = time.time()
    df_with_rules = _add_severity_vectorized(df_with_rules)
    print(f"✅ Severity done: {time.time()-t:.1f}s")

    df_anomalies = df_with_rules[df_with_rules["is_anomaly"] == 1].copy()
    print(f"✅ Anomalies found: {len(df_anomalies)} / {len(df_with_rules)}")

    # --- Build RAG index (top N by severity) ---
    t = time.time()
    if not df_anomalies.empty:
        df_for_rag = df_anomalies.sort_values("severity_score", ascending=False).head(RAG_INDEX_LIMIT)
        embeddings, texts, metadata = embed_anomalies(df_for_rag)
        vector_store.build(embeddings, texts, metadata)
    print(f"✅ RAG index done: {time.time()-t:.1f}s")

    # --- Stats ---
    t = time.time()
    flagged = len(df_anomalies)
    severity_counts = df_anomalies["severity_level"].value_counts().to_dict() if flagged else {}

    all_violations = []
    for v_list in df_anomalies["rule_violations"]:
        all_violations.extend([v["policy_name"] for v in v_list])
    top_policies = Counter(all_violations).most_common(5)

    anomaly_records = _serialize_anomalies(df_anomalies)
    print(f"✅ Serialization done: {time.time()-t:.1f}s")

    return {
        "total_records": total_raw,
        "total_anomalies": flagged,
        "anomaly_rate": round(flagged / len(df_with_rules) * 100, 2),
        "severity_breakdown": severity_counts,
        "top_violated_policies": [{"policy": p, "count": c} for p, c in top_policies],
        "rag_index_size": vector_store.size(),
        "anomalies": anomaly_records,
    }


def _batch_ml_predict(X: pd.DataFrame):
    """Train on 30k sample, predict on all rows in batches."""
    model = AnomalyModel()
    train_size = min(30_000, len(X))
    X_train = X.sample(n=train_size, random_state=42) if len(X) > train_size else X
    model.train(X_train)

    all_flags = []
    all_scores = []
    for start in range(0, len(X), ML_BATCH_SIZE):
        batch = X.iloc[start:start + ML_BATCH_SIZE]
        result = model.predict(batch)
        all_flags.extend(result["ml_anomaly_flag"].tolist())
        all_scores.extend(result["ml_anomaly_score"].tolist())

    return all_flags, all_scores


def _add_severity_vectorized(df: pd.DataFrame) -> pd.DataFrame:
    ml_scores = df["ml_anomaly_score"].values

    def max_rule_score(violations):
        if not violations:
            return 0.0
        return max((lo + hi) / 2 for v in violations for lo, hi in [v.get("severity_range", [0.3, 0.5])])

    rule_scores = np.array([max_rule_score(v) for v in df["rule_violations"]])
    has_violations = rule_scores > 0

    composite = np.where(
        has_violations,
        ml_scores * 0.4 + rule_scores * 0.6,
        ml_scores * 0.4
    ).clip(0, 1)

    levels = pd.cut(
        composite,
        bins=[-0.001, 0.25, 0.5, 0.75, 1.0],
        labels=["low", "medium", "high", "critical"]
    ).astype(str)

    def get_factors(row):
        factors = []
        if row["ml_anomaly_score"] > 0.5:
            factors.append(f"ML anomaly score: {row['ml_anomaly_score']:.2f}")
        for v in row["rule_violations"]:
            factors.append(v.get("policy_name", ""))
        return factors

    df["severity_score"] = np.round(composite, 4)
    df["severity_level"] = levels
    df["contributing_factors"] = df.apply(get_factors, axis=1)
    return df


def _serialize_anomalies(df: pd.DataFrame) -> list:
    key_cols = [
        "Invoice_No_", "Date", "Item_Name", "Order_Type", "Order_Source",
        "Payment_Type", "Status", "Sub_Total", "Discount", "Tax", "Final_Total",
        "CGST_Amount", "SGST_Amount", "VAT_Amount", "Service_Charge_Amount",
        "Is_Online", "Was_Modified", "Modification_Reason",
        "ml_anomaly_flag", "ml_anomaly_score",
        "rule_flag", "rule_violations",
        "severity_score", "severity_level", "contributing_factors",
    ]
    available = [c for c in key_cols if c in df.columns]
    subset = df[available].copy()

    for col in subset.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        subset[col] = subset[col].astype(str)
    for col in subset.select_dtypes(include=[np.integer]).columns:
        subset[col] = subset[col].astype(int)
    for col in subset.select_dtypes(include=[np.floating]).columns:
        subset[col] = subset[col].astype(float)

    return subset.to_dict(orient="records")
