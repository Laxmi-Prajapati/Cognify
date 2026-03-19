import datetime
from pymongo import MongoClient, DESCENDING
from bson.objectid import ObjectId
from app.config import settings


class AuditRepository:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB]
        self.audits = self.db["audits"]

    def save_audit(self, uid: str, audit_result: dict) -> str:
        """Saves full audit result for a user. Returns audit_id."""
        doc = {
            "uid": uid,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "total_records": audit_result.get("total_records"),
            "total_anomalies": audit_result.get("total_anomalies"),
            "anomaly_rate": audit_result.get("anomaly_rate"),
            "severity_breakdown": audit_result.get("severity_breakdown"),
            "top_violated_policies": audit_result.get("top_violated_policies"),
            "rag_index_size": audit_result.get("rag_index_size"),
            "executive_summary": audit_result.get("executive_summary"),
            "anomalies": audit_result.get("anomalies", []),
            "all_records": audit_result.get("all_records", []),
        }
        result = self.audits.insert_one(doc)
        return str(result.inserted_id)

    def get_latest_audit(self, uid: str) -> dict | None:
        """Gets the most recent audit for a user."""
        doc = self.audits.find_one(
            {"uid": uid},
            sort=[("created_at", DESCENDING)]
        )
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_audit_by_id(self, audit_id: str) -> dict | None:
        """Gets a specific audit by ID."""
        doc = self.audits.find_one({"_id": ObjectId(audit_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_audit_history(self, uid: str) -> list:
        """Gets audit history for a user (summary only, no records)."""
        cursor = self.audits.find(
            {"uid": uid},
            {
                "anomalies": 0,
                "all_records": 0,
            },
            sort=[("created_at", DESCENDING)]
        ).limit(10)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
