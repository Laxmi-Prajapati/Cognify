import json
from typing import List, Dict, Any
from groq import Groq
from app.config import settings

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


SYSTEM_PROMPT = """You are Cognify, an expert AI sales auditor for restaurant operations.
You analyze flagged anomalies in sales data and provide clear, actionable audit explanations.

Your responses must:
- Be precise and business-focused
- Reference specific invoice numbers, amounts, and policy violations
- Prioritize critical/high severity issues
- Suggest concrete corrective actions
- Avoid technical jargon — write for a restaurant manager or finance team

Format your response as structured audit findings."""


def explain_anomalies(
    anomaly_chunks: List[Dict],
    question: str = "Summarize the key anomalies and their business impact.",
) -> str:
    """
    Given retrieved anomaly chunks, asks the LLM to explain them in audit terms.
    Token-efficient: only passes the most relevant context.
    """
    if not anomaly_chunks:
        return "No anomalies were retrieved for the given query."

    # Build compact context — only pass what's needed (token efficiency)
    context_parts = []
    for i, chunk in enumerate(anomaly_chunks, 1):
        severity = chunk.get("severity_level", "unknown").upper()
        text = chunk.get("text", "")
        context_parts.append(f"[Anomaly {i} | {severity}]\n{text}")

    context = "\n\n".join(context_parts)

    user_message = f"""AUDIT CONTEXT:
{context}

QUESTION: {question}

Provide a concise audit finding with: 
1. What the issue is
2. Why it matters financially or operationally  
3. Recommended corrective action"""

    client = _get_client()
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
        temperature=0.2,  # Low temp for factual audit responses
    )

    return response.choices[0].message.content


def generate_audit_summary(all_anomalies_summary: Dict[str, Any]) -> str:
    """
    Generates an executive-level audit summary from aggregated stats.
    Token-efficient: passes only counts and top violations.
    """
    summary_text = json.dumps(all_anomalies_summary, indent=2)

    user_message = f"""AUDIT STATISTICS:
{summary_text}

Generate a concise executive audit summary (3-5 sentences) covering:
- Total anomalies found and severity breakdown
- Most common violation types
- Estimated financial risk
- Top recommended actions"""

    client = _get_client()
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=512,
        temperature=0.2,
    )

    return response.choices[0].message.content
