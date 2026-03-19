"use client";

import { useEffect, useState, useMemo } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { ShieldAlert, Search, Download, Filter } from "lucide-react";
import { api } from "@/lib/api";

const SEVERITY_BADGE = {
  critical: "destructive",
  high:     "destructive",
  medium:   "secondary",
  low:      "outline",
};

const SEVERITY_ROW_COLOR = {
  critical: "bg-red-50",
  high:     "bg-orange-50",
  medium:   "bg-yellow-50",
  low:      "bg-green-50",
};

const COLUMNS = [
  { key: "Invoice_No_",           label: "Invoice"      },
  { key: "Date",                  label: "Date"         },
  { key: "Item_Name",             label: "Item"         },
  { key: "Order_Type",            label: "Order Type"   },
  { key: "Order_Source",          label: "Source"       },
  { key: "Payment_Type",          label: "Payment"      },
  { key: "Status",                label: "Status"       },
  { key: "Sub_Total",             label: "Sub Total"    },
  { key: "Discount",              label: "Discount"     },
  { key: "Tax",                   label: "Tax"          },
  { key: "Final_Total",           label: "Final Total"  },
  { key: "CGST_Amount",           label: "CGST"         },
  { key: "SGST_Amount",           label: "SGST"         },
  { key: "Service_Charge_Amount", label: "Svc Chg"      },
  { key: "Is_Online",             label: "Online"       },
  { key: "Was_Modified",          label: "Modified"     },
  { key: "ml_anomaly_flag",       label: "ML Flag"      },
  { key: "ml_anomaly_score",      label: "ML Score"     },
  { key: "rule_flag",             label: "Rule Flag"    },
  { key: "severity_level",        label: "Severity"     },
  { key: "severity_score",        label: "Sev. Score"   },
  { key: "rule_violations",       label: "Violations"   },
];

const CURRENCY_COLS = new Set([
  "Sub_Total", "Discount", "Tax", "Final_Total",
  "CGST_Amount", "SGST_Amount", "Service_Charge_Amount",
]);

const BOOL_COLS = new Set([
  "ml_anomaly_flag", "rule_flag", "Is_Online", "Was_Modified",
]);

const SCORE_COLS = new Set(["ml_anomaly_score", "severity_score"]);

const PAGE_SIZE = 100;

export default function RecordsPage() {
  const [allRows, setAllRows]       = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [search, setSearch]         = useState("");
  const [filter, setFilter]         = useState("all");
  const [flagFilter, setFlagFilter] = useState("all");
  const [page, setPage]             = useState(1);

  useEffect(() => {
    const load = async () => {
      try {
        const audit = await api.getLatestAudit();
        if (audit?.all_records) {
          setAllRows(audit.all_records);
        } else if (audit?.anomalies) {
          // Fallback: only anomalies available
          setAllRows(audit.anomalies);
        } else {
          setAllRows([]);
        }
      } catch (e) {
        if (e.message?.includes("Not logged in") || e.message?.includes("404")) {
          setError("no_audit");
        } else {
          setError(e.message);
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filtered = useMemo(() => {
    let rows = allRows;

    if (flagFilter === "anomalies") rows = rows.filter((r) => r.ml_anomaly_flag || r.rule_flag);
    if (flagFilter === "clean")     rows = rows.filter((r) => !r.ml_anomaly_flag && !r.rule_flag);
    if (filter !== "all")           rows = rows.filter((r) => r.severity_level === filter);

    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter((r) =>
        String(r.Invoice_No_ || "").toLowerCase().includes(q) ||
        String(r.Item_Name   || "").toLowerCase().includes(q) ||
        String(r.Status      || "").toLowerCase().includes(q) ||
        String(r.Order_Source|| "").toLowerCase().includes(q) ||
        (r.rule_violations || []).some((v) => v.policy_name?.toLowerCase().includes(q))
      );
    }

    return rows;
  }, [allRows, filter, flagFilter, search]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated  = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  useEffect(() => { setPage(1); }, [search, filter, flagFilter]);

  const handleExport = () => {
    if (!filtered.length) return;
    const headers = COLUMNS.map((c) => c.label).join(",");
    const rows = filtered.map((row) =>
      COLUMNS.map((c) => {
        const val = row[c.key];
        if (c.key === "rule_violations")
          return `"${(val || []).map((v) => v.policy_name).join("; ")}"`;
        return `"${val ?? ""}"`;
      }).join(",")
    );
    const csv  = [headers, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = "cognify_records.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return (
    <div className="w-full h-screen flex items-center justify-center gap-3">
      <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-gray-900" />
      <p className="text-gray-500">Loading records from database...</p>
    </div>
  );

  if (error === "no_audit" || (!loading && allRows.length === 0)) return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <Header />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] gap-4 text-gray-400">
          <ShieldAlert className="w-16 h-16" />
          <p className="text-lg font-medium">No audit data available</p>
          <p className="text-sm">
            Go to the <a href="/audit" className="text-black underline">Audit page</a> and run an audit first.
          </p>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );

  if (error) return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <Header />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] gap-4 text-red-400">
          <p className="text-lg font-medium">Failed to load records</p>
          <p className="text-sm">{error}</p>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="flex flex-col overflow-hidden h-screen">
        <Header />
        {/* flex flex-col h-[calc(100vh-4rem)] overflow-hidden */}
        <div className="flex flex-col flex-1 overflow-hidden min-h-0">

          {/* Toolbar */}
          <div className="flex flex-wrap items-center gap-3 px-4 py-3 border-b bg-white sticky top-0 z-10">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search invoice, item, violation..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 text-sm"
              />
            </div>

            <div className="flex gap-1">
              {[
                { key: "all",       label: "All"       },
                { key: "anomalies", label: "Anomalies" },
                { key: "clean",     label: "Clean"     },
              ].map((f) => (
                <button key={f.key} onClick={() => setFlagFilter(f.key)}
                  className={`px-3 py-1 text-xs rounded-full border transition ${
                    flagFilter === f.key ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-300 hover:border-gray-500"
                  }`}>
                  {f.label}
                </button>
              ))}
            </div>

            <div className="flex gap-1">
              {["all", "critical", "high", "medium", "low"].map((f) => (
                <button key={f} onClick={() => setFilter(f)}
                  className={`px-3 py-1 text-xs rounded-full border transition ${
                    filter === f ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-300 hover:border-gray-500"
                  }`}>
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>

            <button onClick={handleExport}
              className="ml-auto flex items-center gap-1 px-3 py-1 text-xs rounded-md border border-gray-300 hover:border-gray-500 transition">
              <Download className="w-3 h-3" /> Export CSV
            </button>

            <span className="text-xs text-gray-400 whitespace-nowrap">
              {filtered.length.toLocaleString()} records
            </span>
          </div>

          {/* Table */}
          <div className="overflow-auto flex-1">
            <table className="min-w-full text-sm text-left text-gray-600">
              <thead className="text-xs uppercase text-gray-500 border-b bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-3 py-3 w-8">#</th>
                  {COLUMNS.map((col) => (
                    <th key={col.key} className="px-3 py-3 whitespace-nowrap">{col.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {paginated.map((row, idx) => {
                  const isAnomaly = row.ml_anomaly_flag || row.rule_flag;
                  const rowBg = isAnomaly ? (SEVERITY_ROW_COLOR[row.severity_level] || "") : "";
                  return (
                    <tr key={idx} className={`hover:brightness-95 transition ${rowBg}`}>
                      <td className="px-3 py-2 text-gray-400 text-xs">
                        {(page - 1) * PAGE_SIZE + idx + 1}
                      </td>
                      {COLUMNS.map((col) => {
                        const val = row[col.key];

                        if (col.key === "severity_level") return (
                          <td key={col.key} className="px-3 py-2">
                            {val
                              ? <Badge variant={SEVERITY_BADGE[val] || "outline"}>{val}</Badge>
                              : <span className="text-gray-300">—</span>}
                          </td>
                        );

                        if (col.key === "rule_violations") return (
                          <td key={col.key} className="px-3 py-2 max-w-[240px]">
                            {val?.length
                              ? <div className="flex flex-col gap-1">
                                  {val.map((v, i) => (
                                    <span key={i} className="text-xs text-red-600">• {v.policy_name}</span>
                                  ))}
                                </div>
                              : <span className="text-gray-300 text-xs">—</span>}
                          </td>
                        );

                        if (BOOL_COLS.has(col.key)) return (
                          <td key={col.key} className="px-3 py-2 text-center">
                            {val
                              ? <span className="text-xs font-semibold text-red-500">✓</span>
                              : <span className="text-xs text-gray-300">—</span>}
                          </td>
                        );

                        if (SCORE_COLS.has(col.key)) return (
                          <td key={col.key} className="px-3 py-2 text-xs tabular-nums">
                            {val != null ? Number(val).toFixed(3) : <span className="text-gray-300">—</span>}
                          </td>
                        );

                        if (CURRENCY_COLS.has(col.key)) return (
                          <td key={col.key} className="px-3 py-2 tabular-nums text-xs">
                            {val != null ? `₹${Number(val).toLocaleString()}` : <span className="text-gray-300">—</span>}
                          </td>
                        );

                        if (col.key === "Date") return (
                          <td key={col.key} className="px-3 py-2 whitespace-nowrap text-xs">
                            {val ? String(val).slice(0, 10) : <span className="text-gray-300">—</span>}
                          </td>
                        );

                        return (
                          <td key={col.key} className="px-3 py-2 whitespace-nowrap max-w-[160px] truncate text-xs">
                            {val != null && val !== "" ? String(val) : <span className="text-gray-300">—</span>}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {paginated.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-2">
                <Filter className="w-8 h-8" />
                <p>No records match your filters</p>
              </div>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t bg-white text-xs text-gray-500">
              <span>
                Page {page} of {totalPages} — {((page-1)*PAGE_SIZE)+1}–{Math.min(page*PAGE_SIZE, filtered.length)} of {filtered.length.toLocaleString()}
              </span>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(1, p-1))} disabled={page===1}
                  className="px-3 py-1 rounded border border-gray-300 disabled:opacity-40 hover:border-gray-500 transition">
                  ← Prev
                </button>
                <button onClick={() => setPage((p) => Math.min(totalPages, p+1))} disabled={page===totalPages}
                  className="px-3 py-1 rounded border border-gray-300 disabled:opacity-40 hover:border-gray-500 transition">
                  Next →
                </button>
              </div>
            </div>
          )}

        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

function Header() {
  return (
    <header className="flex h-16 shrink-0 items-center gap-2">
      <div className="flex items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem><BreadcrumbPage>Records</BreadcrumbPage></BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    </header>
  );
}
