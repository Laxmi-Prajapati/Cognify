import Cookies from "js-cookie";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  /**
   * Upload a CSV file and run the full audit pipeline.
   * Returns the full audit result including anomalies, severity breakdown, etc.
   */
  async audit(file) {
    const uid = Cookies.get("uid");
    const formData = new FormData();
    formData.append("file", file);

    // Use combined endpoint if uid available — audits AND saves to MongoDB
    const url = uid
      ? `${BASE_URL}/audit_and_save/${uid}`
      : `${BASE_URL}/api/v1/audit`;

    const res = await fetch(url, { method: "POST", body: formData });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Audit failed (${res.status})`);
    }

    return res.json();
  },

  async getLatestAudit() {
    const uid = Cookies.get("uid");
    if (!uid) throw new Error("Not logged in");

    const res = await fetch(`${BASE_URL}/get_audit/${uid}`);
    if (!res.ok) {
      if (res.status === 404) return null;
      throw new Error(`Failed to fetch audit (${res.status})`);
    }
    return res.json();
  },

  /**
   * Ask a natural language question about the last audited dataset.
   * Requires a prior successful call to audit().
   */
  async ask(question) {
    const res = await fetch(`${BASE_URL}/api/v1/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Ask failed (${res.status})`);
    }

    return res.json();
  },

  /**
   * Check if an audit session is active and how many anomalies are indexed.
   */
  async status() {
    const res = await fetch(`${BASE_URL}/api/v1/audit-status`);
    if (!res.ok) throw new Error("Status check failed");
    return res.json();
  },
};
