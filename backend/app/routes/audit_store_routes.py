import io
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from app.repositories.audit_repo import AuditRepository
from app.services.anomaly_service import run_full_audit

router = APIRouter()
repo = AuditRepository()


class SaveAuditRequest(BaseModel):
    uid: str
    audit_result: dict


@router.post("/save_audit")
def save_audit(body: SaveAuditRequest):
    """Save a completed audit result to MongoDB for a user."""
    try:
        audit_id = repo.save_audit(body.uid, body.audit_result)
        return {"audit_id": audit_id, "message": "Audit saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_audit/{uid}")
def get_latest_audit(uid: str):
    """Get the most recent audit for a user."""
    try:
        audit = repo.get_latest_audit(uid)
        if not audit:
            raise HTTPException(status_code=404, detail="No audit found for this user")
        return audit
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_audit_by_id/{audit_id}")
def get_audit_by_id(audit_id: str):
    """Get a specific audit by its ID."""
    try:
        audit = repo.get_audit_by_id(audit_id)
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")
        return audit
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit_history/{uid}")
def get_audit_history(uid: str):
    """Get audit history (summaries only) for a user."""
    try:
        history = repo.get_audit_history(uid)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit_and_save/{uid}")
async def audit_and_save(uid: str, file: UploadFile = File(...)):
    """
    Combined endpoint: runs full audit AND saves to MongoDB in one call.
    Frontend can use this instead of calling /audit then /save_audit separately.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents), low_memory=False)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=422, detail="Uploaded CSV is empty.")

    try:
        # Run full audit (anomalies only)
        audit_result = run_full_audit(df)

        # Also include all records (clean + anomalies) for the records page
        from app.services.anomaly_service import _serialize_anomalies, _add_severity_vectorized, _batch_ml_predict
        from app.data.data_cleaning import clean_sales_data
        from app.audit.rule_engine import run_rule_engine
        from app.data.feature_engineering import prepare_features
        from app.ml.anomaly_model import AnomalyModel

        df_clean = clean_sales_data(df)
        df_with_rules = run_rule_engine(df_clean)
        X = prepare_features(df_clean)
        model = AnomalyModel()
        ml_flags, ml_scores = _batch_ml_predict(X)
        df_with_rules["ml_anomaly_flag"] = ml_flags
        df_with_rules["ml_anomaly_score"] = ml_scores
        df_with_rules["is_anomaly"] = (
            (df_with_rules["ml_anomaly_flag"] == 1) |
            (df_with_rules["rule_flag"] == 1)
        ).astype(int)
        df_with_rules = _add_severity_vectorized(df_with_rules)
        audit_result["all_records"] = _serialize_anomalies(df_with_rules)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit pipeline error: {str(e)}")

    # Generate executive summary
    try:
        from app.services.rag_service import get_executive_summary
        stats = {k: v for k, v in audit_result.items() if k not in ("anomalies", "all_records")}
        summary = get_executive_summary(stats)
        audit_result["executive_summary"] = summary["executive_summary"]
    except Exception:
        audit_result["executive_summary"] = "Executive summary unavailable."

    # Save to MongoDB

    # Save to MongoDB — cap both arrays to avoid 16MB BSON limit
    try:
        save_payload = dict(audit_result)
        save_payload["all_records"] = save_payload.get("all_records", [])[:1000]
        save_payload["anomalies"] = save_payload.get("anomalies", [])[:1000]
        audit_id = repo.save_audit(uid, save_payload)
        audit_result["audit_id"] = audit_id
        print(f"✅ Saved to MongoDB: {audit_id}")
    except Exception as e:
        print(f"❌ MongoDB save failed: {e}")
        audit_result["audit_id"] = None

    # Save to MongoDB — cap all_records to avoid 16MB BSON limit
    # try:
    #     save_payload = dict(audit_result)
    #     all_records = save_payload.get("all_records", [])
    #     save_payload["all_records"] = all_records[:1000]  # cap at 5000 rows
    #     audit_id = repo.save_audit(uid, save_payload)
    #     audit_result["audit_id"] = audit_id
    #     print(f"✅ Saved to MongoDB: {audit_id} | all_records: {len(save_payload['all_records'])}")
    # except Exception as e:
    #     print(f"❌ MongoDB save failed: {e}")
    #     audit_result["audit_id"] = None

    return audit_result
