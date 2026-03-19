# Cognify Backend v2

AI-powered sales auditing system using a 3-layer detection pipeline + RAG-based explanations.

## Architecture

```
POST /api/v1/audit  (upload CSV)
        ↓
   data_cleaning.py       # parse, normalize, derive Is_Online / Order_Source / Was_Modified
        ↓
   ┌─────────────────────────────────────────┐
   │           3-Layer Detection             │
   │  rule_engine.py  → rule_violations[]    │  ← audit_policies.json (14 policies)
   │  anomaly_model.py → ml_anomaly_flag     │  ← IsolationForest
   │  severity_scorer.py → Low/Med/High/Crit │
   └─────────────────────────────────────────┘
        ↓
   embedder.py            # anomaly row → natural language → sentence-transformers
        ↓
   vector_store.py        # FAISS index (in-memory, per session)
        ↓
   explainer.py           # Groq LLaMA3-70b → executive summary
        ↓
   Response: anomalies[], severity_breakdown, top_policies, executive_summary

POST /api/v1/ask  (question about audited data)
        ↓
   retriever.py           # embed query → FAISS top-k
        ↓
   explainer.py           # LLM answers with retrieved context
```

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

## Run

```bash
python main.py
# or
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/audit` | Upload CSV, run full audit |
| POST | `/api/v1/ask` | Ask a question about the audited data |
| GET | `/api/v1/audit-status` | Check if a session is active |
| GET | `/health` | Health check |

## Audit Policies (14 rules)

1. Incorrect GST Calculation
2. Invalid Service Charge for Online Order
3. Tax Applied to Non-Taxable Item
4. Invalid Payment Method for Online Order
5. Local Order with Aggregator Data
6. Late Cancellation
7. High-Value Cancellation
8. Unapproved Complimentary Order
9. Post-Bill Service Charge Removal
10. Aggregator Payment on Dine-In Order
11. Date and Timestamp Mismatch
12. Discount Without Tax Adjustment
13. Online Order Tax Double-Count Risk
14. Zero Price Item with Tax

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Required. Get from console.groq.com |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `FAISS_TOP_K` | `5` | Number of chunks to retrieve per query |
| `ISOLATION_FOREST_CONTAMINATION` | `0.05` | Expected anomaly rate (5%) |
| `MONGODB_URI` | — | Required. Get from cloud.mongodb.com |