import io
import traceback
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.anomaly_service import run_full_audit
from app.services.rag_service import get_executive_summary

router = APIRouter()


@router.post("/audit")
async def upload_and_audit(file: UploadFile = File(...)):
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
        audit_results = run_full_audit(df)
    except Exception as e:
        print("❌ AUDIT PIPELINE ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Audit pipeline error: {str(e)}")

    try:
        stats_for_summary = {
            "total_records": audit_results["total_records"],
            "total_anomalies": audit_results["total_anomalies"],
            "anomaly_rate": audit_results["anomaly_rate"],
            "severity_breakdown": audit_results["severity_breakdown"],
            "top_violated_policies": audit_results["top_violated_policies"],
        }
        summary = get_executive_summary(stats_for_summary)
        audit_results["executive_summary"] = summary["executive_summary"]
    except Exception as e:
        print(f"⚠️ Executive summary failed: {e}")
        audit_results["executive_summary"] = "Executive summary unavailable."

    return audit_results

# import io
# import pandas as pd
# from fastapi import APIRouter, UploadFile, File, HTTPException
# from app.services.anomaly_service import run_full_audit
# from app.services.rag_service import get_executive_summary
# from app.schemas.requests import AuditResponse

# router = APIRouter()


# @router.post("/audit", response_model=AuditResponse)
# async def upload_and_audit(file: UploadFile = File(...)):
#     """
#     Upload a CSV sales dataset and run the full 3-layer audit:
#     - Rule-based detection
#     - ML anomaly detection (IsolationForest)
#     - Severity scoring
#     - RAG index build for /ask queries

#     Returns flagged anomalies with severity levels and top policy violations.
#     """
#     if not file.filename.endswith(".csv"):
#         raise HTTPException(status_code=400, detail="Only CSV files are supported.")

#     try:
#         contents = await file.read()
#         df = pd.read_csv(io.BytesIO(contents), low_memory=False)
#     except Exception as e:
#         raise HTTPException(status_code=422, detail=f"Failed to parse CSV: {str(e)}")

#     if df.empty:
#         raise HTTPException(status_code=422, detail="Uploaded CSV is empty.")

#     try:
#         audit_results = run_full_audit(df)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Audit pipeline error: {str(e)}")

#     # Generate executive summary via LLM
#     try:
#         stats_for_summary = {
#             "total_records": audit_results["total_records"],
#             "total_anomalies": audit_results["total_anomalies"],
#             "anomaly_rate": audit_results["anomaly_rate"],
#             "severity_breakdown": audit_results["severity_breakdown"],
#             "top_violated_policies": audit_results["top_violated_policies"],
#         }
#         summary = get_executive_summary(stats_for_summary)
#         audit_results["executive_summary"] = summary["executive_summary"]
#     except Exception:
#         audit_results["executive_summary"] = "Executive summary unavailable (check GROQ_API_KEY)."

#     return audit_results
