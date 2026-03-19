"use client";
import { useEffect } from "react";
import { useState } from "react";
import { UploadCloud, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { api } from "@/lib/api";
import Cookies from "js-cookie";

const SEVERITY_COLORS = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high:     "bg-orange-100 text-orange-700 border-orange-200",
  medium:   "bg-yellow-100 text-yellow-700 border-yellow-200",
  low:      "bg-green-100 text-green-700 border-green-200",
};

const SEVERITY_BADGE = {
  critical: "destructive",
  high:     "destructive",
  medium:   "secondary",
  low:      "outline",
};

export default function AuditPage() {
  const [file, setFile]           = useState(null);
  const [result, setResult]       = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState(null);
  const [filter, setFilter]       = useState("all");

  useEffect(() => {
    const stored = localStorage.getItem("cognify_audit_result");
    if (stored) {
      try { setResult(JSON.parse(stored)); } catch {}
    }
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) { setError("Please select a CSV file."); return; }
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const uid = Cookies.get("uid");
      const formData = new FormData();
      formData.append("file", file);

      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const url = uid
        ? `${BASE_URL}/audit_and_save/${uid}`
        : `${BASE_URL}/api/v1/audit`;

      const res = await fetch(url, { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Audit failed (${res.status})`);
      }
      const data = await res.json();
      setResult(data);

      try {
        const summary = {
          total_records: data.total_records,
          total_anomalies: data.total_anomalies,
          anomaly_rate: data.anomaly_rate,
          severity_breakdown: data.severity_breakdown,
          top_violated_policies: data.top_violated_policies,
          rag_index_size: data.rag_index_size,
          executive_summary: data.executive_summary,
          audit_id: data.audit_id,
          anomalies: data.anomalies?.slice(0, 500) ?? [],
        };
        localStorage.setItem("cognify_audit_result", JSON.stringify(summary));
      } catch (e) {
        console.warn("localStorage save failed:", e);
      }
    } catch (err) {
      setError(err.message || "Audit failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const filteredAnomalies = result?.anomalies?.filter(
    (a) => filter === "all" || a.severity_level === filter
  ) ?? [];

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem><BreadcrumbPage>Audit</BreadcrumbPage></BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>

        <main className="flex flex-col h-[calc(100vh-4rem)] overflow-auto">

          {/* Upload Section */}
          <div className="w-full px-4 md:px-6 py-6 bg-white border-b border-gray-200">
            <div className="w-full border-2 border-dashed border-gray-300 rounded-2xl p-8 flex flex-col items-center justify-center gap-4">
              <UploadCloud className="w-10 h-10 text-gray-500" />
              <p className="text-gray-600 text-lg font-medium">
                Upload a CSV file to run the full audit pipeline
              </p>
              <Input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="cursor-pointer bg-muted/50 text-gray-500 max-w-sm"
                disabled={isLoading}
              />
              <button
                onClick={handleUpload}
                disabled={isLoading || !file}
                className="px-6 py-2 border bg-black border-black text-white rounded-md hover:bg-muted/50 hover:text-black transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Running Audit..." : "Run Audit"}
              </button>
              {file && (
                <p className="text-sm text-gray-500">
                  Selected: <span className="font-medium">{file.name}</span>
                  {isLoading && <span className="ml-2 text-blue-500">(Processing ~50s for large files...)</span>}
                </p>
              )}
              {error && <p className="text-sm text-red-500 text-center">{error}</p>}
            </div>
          </div>

          <ScrollArea className="flex-1 w-full px-4 md:px-6 py-6">
            {isLoading ? (
              <div className="w-full flex flex-col items-center justify-center py-12 gap-4">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900" />
                <p className="text-gray-600">Running 3-layer audit pipeline...</p>
                <p className="text-sm text-gray-400">Rule engine → IsolationForest → RAG indexing</p>
              </div>
            ) : result ? (
              <div className="space-y-6">

                {/* Stats Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: "Total Records", value: result.total_records?.toLocaleString() },
                    { label: "Anomalies Found", value: result.total_anomalies?.toLocaleString() },
                    { label: "Anomaly Rate", value: `${result.anomaly_rate}%` },
                    { label: "RAG Index Size", value: result.rag_index_size },
                  ].map((stat) => (
                    <div key={stat.label} className="bg-muted/50 rounded-xl p-4">
                      <p className="text-sm text-gray-500">{stat.label}</p>
                      <p className="text-2xl font-semibold mt-1">{stat.value}</p>
                    </div>
                  ))}
                </div>

                {/* Severity Breakdown */}
                <div className="bg-muted/50 rounded-xl p-4">
                  <p className="text-sm font-semibold text-gray-700 mb-3">Severity Breakdown</p>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(result.severity_breakdown || {}).map(([level, count]) => (
                      <div key={level} className={`rounded-lg px-4 py-2 border text-sm font-medium ${SEVERITY_COLORS[level] || "bg-gray-100 text-gray-700"}`}>
                        {level.charAt(0).toUpperCase() + level.slice(1)}: {count}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Top Violated Policies */}
                <div className="bg-muted/50 rounded-xl p-4">
                  <p className="text-sm font-semibold text-gray-700 mb-3">Top Violated Policies</p>
                  <div className="space-y-2">
                    {result.top_violated_policies?.map((p) => (
                      <div key={p.policy} className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">{p.policy}</span>
                        <Badge variant="secondary">{p.count} violations</Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Executive Summary */}
                {result.executive_summary && (
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Info className="w-4 h-4 text-blue-600" />
                      <p className="text-sm font-semibold text-blue-700">AI Executive Summary</p>
                    </div>
                    <p className="text-sm text-blue-800 leading-relaxed">{result.executive_summary}</p>
                  </div>
                )}

                {/* Anomaly Table */}
                <div className="bg-white rounded-xl border border-gray-200">
                  <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
                    <p className="text-sm font-semibold text-gray-700">
                      Flagged Anomalies ({filteredAnomalies.length})
                    </p>
                    <div className="flex gap-2">
                      {["all", "critical", "high", "medium", "low"].map((f) => (
                        <button
                          key={f}
                          onClick={() => setFilter(f)}
                          className={`px-3 py-1 text-xs rounded-full border transition ${
                            filter === f ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-300 hover:border-gray-500"
                          }`}
                        >
                          {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm text-left text-gray-600">
                      <thead className="text-xs uppercase text-gray-500 border-b bg-gray-50">
                        <tr>
                          {["Invoice", "Date", "Item", "Order Type", "Status", "Final Total", "Severity", "Violations"].map((col) => (
                            <th key={col} className="px-4 py-3 whitespace-nowrap">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {filteredAnomalies.slice(0, 200).map((row, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 font-medium">{row.Invoice_No_ || "-"}</td>
                            <td className="px-4 py-2 whitespace-nowrap">{row.Date ? String(row.Date).slice(0, 10) : "-"}</td>
                            <td className="px-4 py-2 max-w-[160px] truncate">{row.Item_Name || "-"}</td>
                            <td className="px-4 py-2 whitespace-nowrap">{row.Order_Type || "-"}</td>
                            <td className="px-4 py-2">{row.Status || "-"}</td>
                            <td className="px-4 py-2 whitespace-nowrap">₹{row.Final_Total?.toLocaleString() || "-"}</td>
                            <td className="px-4 py-2">
                              <Badge variant={SEVERITY_BADGE[row.severity_level] || "outline"}>
                                {row.severity_level || "-"}
                              </Badge>
                            </td>
                            <td className="px-4 py-2 max-w-[200px]">
                              <span className="text-xs text-gray-500">
                                {row.rule_violations?.map((v) => v.policy_name).join(", ") || (row.ml_anomaly_flag ? "ML detected" : "-")}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {filteredAnomalies.length > 200 && (
                      <p className="text-xs text-gray-400 text-center py-3">
                        Showing 200 of {filteredAnomalies.length} anomalies. Use the /ask endpoint to query specific patterns.
                      </p>
                    )}
                  </div>
                </div>

              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-3">
                <UploadCloud className="w-12 h-12" />
                <p>Upload a CSV file to start the audit</p>
              </div>
            )}
          </ScrollArea>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
