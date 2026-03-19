import json
import pandas as pd
import numpy as np
from typing import List, Dict
from app.config import settings

_policies_cache = None


def _load_policies() -> List[Dict]:
    global _policies_cache
    if _policies_cache is None:
        with open(settings.AUDIT_POLICIES_PATH, "r") as f:
            _policies_cache = json.load(f)["audit_policies"]
    return _policies_cache


def run_rule_engine(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fully vectorized rule engine.
    Pre-computes all string columns once to avoid repeated .str operations.
    """
    df = df.copy()
    n = len(df)

    # --- Pre-compute all string cols ONCE ---
    order_source = df["Order_Source"].str.lower().str.strip() if "Order_Source" in df.columns else pd.Series([""] * n, index=df.index)
    status       = df["Status"].str.lower().str.strip() if "Status" in df.columns else pd.Series([""] * n, index=df.index)
    payment      = df["Payment_Type"].str.lower().str.strip() if "Payment_Type" in df.columns else pd.Series([""] * n, index=df.index)
    order_type   = df["Order_Type"].str.lower().str.strip() if "Order_Type" in df.columns else pd.Series([""] * n, index=df.index)
    mod_reason   = df["Modification_Reason"].str.lower() if "Modification_Reason" in df.columns else pd.Series([""] * n, index=df.index)
    category     = df["Category"].str.lower().str.strip() if "Category" in df.columns else pd.Series([""] * n, index=df.index)

    # Bar/alcohol items use VAT not GST — exclude from GST check
    is_bar_item = category.str.contains(
        "bar|wine|beer|whisky|whiskey|scotch|cocktail|mocktail|beverage|breezer",
        na=False
    )

    # --- Pre-compute numeric cols ---
    def num(col, default=0):
        return df[col] if col in df.columns else pd.Series([default] * n, index=df.index)

    is_online       = num("Is_Online")
    sub_total       = num("Sub_Total")
    cgst            = num("CGST_Amount")
    sgst            = num("SGST_Amount")
    vat             = num("VAT_Amount")
    tax             = num("Tax")
    discount        = num("Discount")
    sc              = num("Service_Charge_Amount")
    non_taxable     = num("Non_Taxable")
    prep_z          = num("Food_Preparation_Time_Z")
    prep_s          = num("Food_Preparation_Time_S")
    cancelled_total = num("Cancelled_Invoice_Total_co")
    online_tax_z    = num("Online_Tax_Calculated_z")
    online_tax_s    = num("Online_Tax_Calculated_s")
    price           = num("Price")
    was_modified    = num("Was_Modified")
    has_agg         = num("Has_Aggregator_No")

    assign_empty = (
        df["Assign_To"].isna() | (df["Assign_To"].astype(str).str.strip().isin(["", "nan"]))
        if "Assign_To" in df.columns
        else pd.Series([True] * n, index=df.index)
    )

    masks = {
        # Only flag food items (non-bar, VAT=0) — bar items use VAT not 5% GST
        "Incorrect GST Calculation": (
            (order_source == "local") &
            (sub_total > 0) &
            (non_taxable == 0) &
            (~is_bar_item) &
            (vat == 0) &
            ((cgst + sgst - 0.05 * sub_total).abs() > 1)
        ),
        "Invalid Service Charge for Online Order": (
            (is_online == 1) & (sc > 0)
        ),
        "Tax Applied to Non-Taxable Item": (
            (non_taxable > 0) & ((cgst + sgst + vat) > 0)
        ),
        "Invalid Payment Method for Online Order": (
            (is_online == 1) &
            (~payment.isin({"online", "other [zomato pay]", "other [paytm]"}))
        ),
        "Local Order with Aggregator Data": (
            (order_source == "local") & (has_agg == 1)
        ),
        "Late Cancellation": (
            status.str.contains("cancelled", na=False) &
            ((prep_z > 30) | (prep_s > 30))
        ),
        "High-Value Cancellation": (
            status.str.contains("cancelled", na=False) &
            (cancelled_total > 1000)
        ),
        "Unapproved Complimentary Order": (
            (status == "complimentary") & assign_empty
        ),
        "Post-Bill Service Charge Removal": (
            (was_modified == 1) & mod_reason.str.contains("sc", na=False)
        ),
        # REMOVED: Aggregator Payment on Dine-In — Paytm/Zomato Pay are valid dine-in methods
        # REMOVED: Date and Timestamp Mismatch — late-night orders crossing midnight are normal
        "Discount Without Tax Adjustment": (
            (discount > 0) & (sub_total > discount) &
            (tax > ((sub_total - discount) * 0.10 + 2))
        ),
        "Online Order Tax Double-Count Risk": (
            (is_online == 1) & (tax > 0) &
            ((online_tax_z > 0) | (online_tax_s > 0))
        ),
        "Zero Price Item with Tax": (
            (price == 0) & (sub_total == 0) &
            ((cgst + sgst + vat + tax) > 0)
        ),
    }

    # --- Build flag column ---
    flag_matrix = pd.DataFrame(masks, index=df.index)
    df["rule_flag"] = flag_matrix.any(axis=1).astype(int)

    # --- Build violations list ---
    policies = {p["policy_name"]: p for p in _load_policies()}
    violations = [[] for _ in range(n)]

    for policy_name, mask in masks.items():
        policy = policies.get(policy_name, {})
        flagged_indices = np.where(mask.values)[0]
        if len(flagged_indices) == 0:
            continue
        entry = {
            "policy_name": policy_name,
            "severity_range": policy.get("severity_range", [0.3, 0.5]),
            "action": policy.get("action", ""),
        }
        for idx in flagged_indices:
            violations[idx].append(entry)

    df["rule_violations"] = violations
    return df
