import pandas as pd
import numpy as np

NUMERIC_COLS = [
    "Price", "Qty_", "Sub_Total", "Discount", "Tax", "Final_Total",
    "CGST_Amount", "SGST_Amount", "VAT_Amount", "Service_Charge_Amount",
    "CGST_Rate", "SGST_Rate", "VAT_Rate", "Service_Charge_Rate",
    "Online_Tax_Calculated_z", "Online_Tax_Calculated_s",
    "Cancelled_Invoice_Total_co", "Food_Preparation_Time_Z",
    "Food_Preparation_Time_S", "Non_Taxable", "Covers",
]

CATEGORICAL_COLS = ["Order_Type", "Payment_Type", "Status", "Category", "Area"]

# Only parse the datetime cols we actually USE in rules/features
# Skipping the 100+ aggregator timestamp cols that are rarely populated
ESSENTIAL_DATETIME_COLS = ["Date", "Timestamp"]


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- Only parse the 2 datetime cols we actually need ---
    # Date: dd-mm-yyyy format
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True, format="mixed")

    # Timestamp: UTC format
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"], errors="coerce", utc=True
        ).dt.tz_localize(None)

    # --- Numeric normalization (only cols that exist) ---
    existing_numeric = [c for c in NUMERIC_COLS if c in df.columns]
    for col in existing_numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0)

    # --- Categorical normalization ---
    existing_cat = [c for c in CATEGORICAL_COLS if c in df.columns]
    for col in existing_cat:
        df[col] = df[col].fillna("missing").astype(str).str.strip().str.title()

    # --- Derived: Order source (vectorized) ---
    order_area = df.get("Area", pd.Series(dtype=str)).fillna("").astype(str).str.lower()
    order_type = df.get("Order_Type", pd.Series(dtype=str)).fillna("").astype(str).str.lower()

    has_zomato = (
        df.get("Order_From_z", pd.Series(dtype=object)).notna() &
        (df.get("Order_From_z", pd.Series(dtype=object)).astype(str).str.strip() != "") &
        (df.get("Order_From_z", pd.Series(dtype=object)).astype(str).str.strip() != "nan")
    )
    has_swiggy = (
        df.get("Order_From_s", pd.Series(dtype=object)).notna() &
        (df.get("Order_From_s", pd.Series(dtype=object)).astype(str).str.strip() != "") &
        (df.get("Order_From_s", pd.Series(dtype=object)).astype(str).str.strip() != "nan")
    )

    # Also detect online from Area column (Zomato/Swiggy appear there)
    area_is_zomato = order_area.str.contains("zomato", na=False)
    area_is_swiggy = order_area.str.contains("swiggy", na=False)

    df["Is_Online"] = (has_zomato | has_swiggy | area_is_zomato | area_is_swiggy).astype(int)
    df["Order_Source"] = np.select(
        [has_zomato | area_is_zomato, has_swiggy | area_is_swiggy],
        ["Zomato", "Swiggy"],
        default="Local"
    )

    # --- Derived: Date vs Timestamp mismatch ---
    if "Date" in df.columns and "Timestamp" in df.columns:
        df["Date_Timestamp_Mismatch"] = (
            df["Date"].dt.date != df["Timestamp"].dt.date
        ).astype(int)
    else:
        df["Date_Timestamp_Mismatch"] = 0

    # --- Derived: Post-bill modification ---
    if "modify_comment" in df.columns:
        df["Was_Modified"] = df["modify_comment"].notna().astype(int)
        df["Modification_Reason"] = df["modify_comment"].fillna("")
    else:
        df["Was_Modified"] = 0
        df["Modification_Reason"] = ""

    # --- Derived: Aggregator order number present ---
    agg_z = df.get("Aggregator_Order_No_z", pd.Series(dtype=object))
    agg_s = df.get("Aggregator_Order_No_s", pd.Series(dtype=object))
    df["Has_Aggregator_No"] = (
        (agg_z.notna() & (agg_z.astype(str).str.strip().isin(["", "nan"]) == False)) |
        (agg_s.notna() & (agg_s.astype(str).str.strip().isin(["", "nan"]) == False))
    ).astype(int)

    df.drop_duplicates(inplace=True)

    return df
