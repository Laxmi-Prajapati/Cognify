from typing import Dict, Any
from app.rag.retriever import retrieve
from app.rag.explainer import explain_anomalies, generate_audit_summary
from app.rag.vector_store import vector_store


def ask_about_anomalies(question: str) -> Dict[str, Any]:
    """
    Retrieves relevant anomaly chunks and asks the LLM to answer
    the user's question about the uploaded dataset.
    """
    if not vector_store.is_ready():
        return {
            "answer": "No audit data available. Please upload and audit a dataset first.",
            "retrieved_chunks": 0,
        }

    chunks = retrieve(question)
    answer = explain_anomalies(chunks, question=question)

    return {
        "answer": answer,
        "retrieved_chunks": len(chunks),
        "top_invoices": [c.get("invoice_no") for c in chunks],
    }


def get_executive_summary(audit_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates an AI executive summary from audit statistics.
    """
    summary = generate_audit_summary(audit_stats)
    return {"executive_summary": summary}
