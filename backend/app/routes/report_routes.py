from fastapi import APIRouter, HTTPException
from app.schemas.requests import AskRequest, AskResponse
from app.services.rag_service import ask_about_anomalies
from app.rag.vector_store import vector_store

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Ask a natural language question about the audited dataset.
    Retrieves relevant anomaly chunks via FAISS and generates an LLM explanation.

    Example questions:
    - "Which invoices have tax calculation errors?"
    - "What are the high severity anomalies?"
    - "Are there any suspicious cancellations?"
    - "Explain the service charge violations"
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not vector_store.is_ready():
        raise HTTPException(
            status_code=400,
            detail="No audit data loaded. Please POST a CSV to /api/v1/audit first."
        )

    try:
        result = ask_about_anomalies(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {str(e)}")

    return result


@router.get("/audit-status")
def audit_status():
    """Returns whether an audit session is active and index stats."""
    return {
        "session_active": vector_store.is_ready(),
        "indexed_anomalies": vector_store.size(),
    }
