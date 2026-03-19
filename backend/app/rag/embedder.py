import pandas as pd
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from app.config import settings

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def row_to_text(row: pd.Series) -> str:
    """
    Converts a flagged anomaly row to a human-readable text chunk for embedding.
    Focuses on the most audit-relevant fields.
    """
    parts = []

    inv = row.get("Invoice_No_", "N/A")
    parts.append(f"Invoice {inv}")

    date = row.get("Date", "")
    if pd.notna(date) and str(date) not in ("", "NaT"):
        parts.append(f"dated {str(date)[:10]}")

    item = row.get("Item_Name", "")
    if item and str(item) != "nan":
        parts.append(f"item '{item}'")

    source = row.get("Order_Source", "")
    order_type = row.get("Order_Type", "")
    if source:
        parts.append(f"order source: {source} ({order_type})")

    sub = row.get("Sub_Total", 0)
    disc = row.get("Discount", 0)
    tax = row.get("Tax", 0)
    final = row.get("Final_Total", 0)
    parts.append(f"Sub_Total=₹{sub}, Discount=₹{disc}, Tax=₹{tax}, Final=₹{final}")

    cgst = row.get("CGST_Amount", 0)
    sgst = row.get("SGST_Amount", 0)
    vat = row.get("VAT_Amount", 0)
    sc = row.get("Service_Charge_Amount", 0)
    parts.append(f"CGST=₹{cgst}, SGST=₹{sgst}, VAT=₹{vat}, ServiceCharge=₹{sc}")

    status = row.get("Status", "")
    payment = row.get("Payment_Type", "")
    parts.append(f"Status: {status}, Payment: {payment}")

    assign = row.get("Assign_To", "")
    if assign and str(assign) not in ("nan", ""):
        parts.append(f"Assigned to: {assign}")

    is_online = row.get("Is_Online", 0)
    if is_online:
        parts.append("flagged as online/aggregator order")

    mod_reason = row.get("Modification_Reason", "")
    if mod_reason and str(mod_reason) not in ("nan", ""):
        parts.append(f"post-bill modification: '{mod_reason}'")

    violations = row.get("rule_violations", [])
    if violations:
        policy_names = [v["policy_name"] for v in violations]
        parts.append(f"Rule violations: {', '.join(policy_names)}")

    severity = row.get("severity_level", "")
    if severity:
        parts.append(f"Severity: {severity} (score: {row.get('severity_score', 0):.2f})")

    return ". ".join(parts) + "."


def embed_anomalies(
    df_anomalies: pd.DataFrame,
) -> Tuple[np.ndarray, List[str], List[dict]]:
    """
    Converts each anomaly row to text, embeds it, and returns:
      - embeddings: np.ndarray of shape (n, embedding_dim)
      - texts: list of text chunks
      - metadata: list of dicts with invoice/severity info for retrieval
    """
    model = _get_model()
    texts = []
    metadata = []

    for idx, row in df_anomalies.iterrows():
        text = row_to_text(row)
        texts.append(text)
        metadata.append({
            "index": int(idx),
            "invoice_no": str(row.get("Invoice_No_", "")),
            "severity_level": str(row.get("severity_level", "low")),
            "severity_score": float(row.get("severity_score", 0.0)),
            "rule_violations": row.get("rule_violations", []),
            "text": text,
        })

    embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
    return np.array(embeddings, dtype="float32"), texts, metadata
