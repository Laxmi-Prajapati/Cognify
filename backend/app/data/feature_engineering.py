import pandas as pd

NUMERIC_FEATURES = [
    "Price", "Qty_", "Sub_Total", "Discount", "Tax", "Final_Total",
    "CGST_Amount", "SGST_Amount", "VAT_Amount", "Service_Charge_Amount",
    "Is_Online",
]

CATEGORICAL_FEATURES = ["Payment_Type", "Order_Type", "Status", "Order_Source"]

TIME_FEATURE = "Timestamp"


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares feature matrix for IsolationForest.
    Returns a numeric DataFrame with no NaNs.
    """
    available_numeric = [c for c in NUMERIC_FEATURES if c in df.columns]
    df_model = df[available_numeric].copy()

    # Time features
    if TIME_FEATURE in df.columns:
        ts = pd.to_datetime(df[TIME_FEATURE], errors="coerce")
        df_model["hour"] = ts.dt.hour.fillna(0).astype(int)
        df_model["day"] = ts.dt.day.fillna(0).astype(int)
        df_model["month"] = ts.dt.month.fillna(0).astype(int)
        df_model["weekday"] = ts.dt.weekday.fillna(0).astype(int)

    # One-hot encode categoricals
    available_cat = [c for c in CATEGORICAL_FEATURES if c in df.columns]
    if available_cat:
        cat_df = df[available_cat].copy()
        for col in available_cat:
            cat_df[col] = cat_df[col].fillna("missing").astype(str)
        cat_encoded = pd.get_dummies(cat_df, columns=available_cat, drop_first=True)
        df_model = pd.concat([df_model, cat_encoded], axis=1)

    df_model = df_model.fillna(0)

    # Ensure all columns are numeric
    for col in df_model.columns:
        df_model[col] = pd.to_numeric(df_model[col], errors="coerce").fillna(0)

    return df_model
