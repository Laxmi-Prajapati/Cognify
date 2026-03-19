from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.anomaly_routes import router as anomaly_router
from app.routes.report_routes import router as report_router
from app.routes.user_routes import router as user_router
from app.routes.audit_store_routes import router as audit_store_router

app = FastAPI(
    title="Cognify API",
    description="AI-powered sales auditing system with RAG-based anomaly detection",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# User auth routes (no prefix)
app.include_router(user_router)

# Audit store routes (no prefix — /save_audit, /get_audit, etc.)
app.include_router(audit_store_router)

# Audit + RAG routes
app.include_router(anomaly_router, prefix="/api/v1", tags=["Anomaly Detection"])
app.include_router(report_router, prefix="/api/v1", tags=["Audit Reports"])


@app.get("/")
def root():
    return {"message": "Cognify Backend Running", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}



# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.routes.anomaly_routes import router as anomaly_router
# from app.routes.report_routes import router as report_router

# app = FastAPI(
#     title="Cognify API",
#     description="AI-powered sales auditing system with RAG-based anomaly detection",
#     version="2.0.0",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(anomaly_router, prefix="/api/v1", tags=["Anomaly Detection"])
# app.include_router(report_router, prefix="/api/v1", tags=["Audit Reports"])


# @app.get("/")
# def root():
#     return {"message": "Cognify Backend Running", "version": "2.0.0"}


# @app.get("/health")
# def health():
#     return {"status": "ok"}
