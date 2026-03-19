from pydantic import BaseModel
from typing import List, Optional, Any, Dict


# ── Requests ──────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str


# ── Responses ─────────────────────────────────────────────

class PolicyViolation(BaseModel):
    policy_name: str
    severity_range: List[float]
    action: str


class AnomalyRecord(BaseModel):
    Invoice_No_: Optional[str] = None
    Date: Optional[str] = None
    Item_Name: Optional[str] = None
    Order_Type: Optional[str] = None
    Order_Source: Optional[str] = None
    Payment_Type: Optional[str] = None
    Status: Optional[str] = None
    Sub_Total: Optional[float] = None
    Discount: Optional[float] = None
    Tax: Optional[float] = None
    Final_Total: Optional[float] = None
    ml_anomaly_flag: Optional[int] = None
    ml_anomaly_score: Optional[float] = None
    rule_flag: Optional[int] = None
    rule_violations: Optional[List[Dict[str, Any]]] = None
    severity_score: Optional[float] = None
    severity_level: Optional[str] = None
    contributing_factors: Optional[List[str]] = None


class SeverityBreakdown(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class TopPolicy(BaseModel):
    policy: str
    count: int


class AuditResponse(BaseModel):
    total_records: int
    total_anomalies: int
    anomaly_rate: float
    severity_breakdown: Dict[str, int]
    top_violated_policies: List[TopPolicy]
    rag_index_size: int
    executive_summary: Optional[str] = None
    anomalies: List[Dict[str, Any]]


class AskResponse(BaseModel):
    answer: str
    retrieved_chunks: int
    top_invoices: List[Optional[str]]
