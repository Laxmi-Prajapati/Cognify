"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from "react";
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Card, CardTitle, CardHeader, CardContent, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Hash, TriangleAlert, TrendingUp, ShieldAlert } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, CartesianGrid, LineChart, Line,
} from "recharts";

const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#64748b"];

const SEVERITY_ORDER = ["critical", "high", "medium", "low"];

export default function DashboardPage() {
  const [report, setReport]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter]   = useState("all");

  useEffect(() => {
    // Load last audit result from localStorage (set by audit page after successful run)
    const stored = localStorage.getItem("cognify_audit_result");
    if (stored) {
      try { setReport(JSON.parse(stored)); } catch {}
    }
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="w-full h-screen flex flex-col items-center justify-center gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900" />
        <p className="text-muted-foreground">Loading dashboard...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2">
            <div className="flex items-center gap-2 px-4">
              <SidebarTrigger className="-ml-1" />
              <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem><BreadcrumbPage>Dashboard</BreadcrumbPage></BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] gap-4 text-gray-400">
            <ShieldAlert className="w-16 h-16" />
            <p className="text-lg font-medium">No audit data available</p>
            <p className="text-sm">Go to the <a href="/audit" className="text-black underline">Audit page</a> and upload a CSV to generate a report.</p>
          </div>
        </SidebarInset>
      </SidebarProvider>
    );
  }

  // Build chart data from audit result
  const severityData = SEVERITY_ORDER
    .filter((s) => report.severity_breakdown?.[s])
    .map((s) => ({
      name: s.charAt(0).toUpperCase() + s.slice(1),
      value: report.severity_breakdown[s],
    }));

  const policyData = (report.top_violated_policies || []).map((p) => ({
    name: p.policy.length > 30 ? p.policy.slice(0, 30) + "…" : p.policy,
    value: p.count,
  }));

  const mlVsRule = [
    { name: "ML Only", value: report.anomalies?.filter((a) => a.ml_anomaly_flag && !a.rule_flag).length || 0 },
    { name: "Rule Only", value: report.anomalies?.filter((a) => !a.ml_anomaly_flag && a.rule_flag).length || 0 },
    { name: "Both", value: report.anomalies?.filter((a) => a.ml_anomaly_flag && a.rule_flag).length || 0 },
  ];

  const filtered = filter === "all"
    ? report.anomalies
    : report.anomalies?.filter((a) => a.severity_level === filter);

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem><BreadcrumbPage>Dashboard</BreadcrumbPage></BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>

        <ScrollArea className="h-[calc(100vh-4rem)]">
          <div className="flex flex-col gap-6 p-4 pt-4">

            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Total Records",   value: report.total_records?.toLocaleString(),   icon: <Hash size={20} color="white" /> },
                { label: "Total Anomalies", value: report.total_anomalies?.toLocaleString(),  icon: <TriangleAlert size={20} color="white" /> },
                { label: "Anomaly Rate",    value: `${report.anomaly_rate}%`,                 icon: <TrendingUp size={20} color="white" /> },
                { label: "RAG Indexed",     value: report.rag_index_size,                     icon: <ShieldAlert size={20} color="white" /> },
              ].map((s) => (
                <Card key={s.label} className="border-none shadow-none bg-muted/50">
                  <CardHeader>
                    <div className="flex justify-between items-center gap-2">
                      <div>
                        <CardDescription>{s.label}</CardDescription>
                        <CardTitle className="text-3xl font-semibold tabular-nums mt-1">{s.value}</CardTitle>
                      </div>
                      <div className="rounded-2xl bg-primary p-4 flex items-center justify-center">{s.icon}</div>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>

            {/* Executive Summary */}
            {report.executive_summary && (
              <Card className="border-none shadow-none bg-blue-50 border border-blue-100">
                <CardHeader>
                  <CardDescription className="text-blue-600 font-medium">AI Executive Summary</CardDescription>
                  <p className="text-sm text-blue-800 leading-relaxed mt-1">{report.executive_summary}</p>
                </CardHeader>
              </Card>
            )}

            {/* Charts Row */}
            <div className="grid md:grid-cols-3 gap-4">

              {/* Severity Pie */}
              <Card className="border-none shadow-none bg-muted/50">
                <CardHeader><CardTitle className="text-base">Severity Distribution</CardTitle></CardHeader>
                <CardContent className="h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={severityData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                        {severityData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Top Policies Bar */}
              <Card className="border-none shadow-none bg-muted/50 md:col-span-2">
                <CardHeader><CardTitle className="text-base">Top Violated Policies</CardTitle></CardHeader>
                <CardContent className="h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={policyData} layout="vertical" margin={{ left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#334155">
                        {policyData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

            </div>

            {/* ML vs Rule detection breakdown */}
            <Card className="border-none shadow-none bg-muted/50">
              <CardHeader><CardTitle className="text-base">Detection Method Breakdown</CardTitle></CardHeader>
              <CardContent className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={mlVsRule}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#475569">
                      {mlVsRule.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Anomaly Table */}
            <Card className="border-none shadow-none bg-muted/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Anomaly Records ({filtered?.length?.toLocaleString()})</CardTitle>
                  <div className="flex gap-2">
                    {["all", ...SEVERITY_ORDER].map((f) => (
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
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm text-left text-gray-600">
                    <thead className="text-xs uppercase text-gray-500 border-b bg-gray-50">
                      <tr>
                        {["Invoice", "Date", "Item", "Source", "Status", "Final Total", "Severity", "Violations"].map((col) => (
                          <th key={col} className="px-4 py-3 whitespace-nowrap">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {filtered?.slice(0, 100).map((row, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-2 font-medium">{row.Invoice_No_ || "-"}</td>
                          <td className="px-4 py-2 whitespace-nowrap">{row.Date ? String(row.Date).slice(0, 10) : "-"}</td>
                          <td className="px-4 py-2 max-w-[140px] truncate">{row.Item_Name || "-"}</td>
                          <td className="px-4 py-2">{row.Order_Source || "-"}</td>
                          <td className="px-4 py-2">{row.Status || "-"}</td>
                          <td className="px-4 py-2 whitespace-nowrap">₹{row.Final_Total?.toLocaleString() || "-"}</td>
                          <td className="px-4 py-2">
                            <Badge variant={row.severity_level === "critical" || row.severity_level === "high" ? "destructive" : "secondary"}>
                              {row.severity_level || "-"}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 max-w-[200px] text-xs text-gray-500 truncate">
                            {row.rule_violations?.map((v) => v.policy_name).join(", ") || (row.ml_anomaly_flag ? "ML detected" : "-")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {(filtered?.length || 0) > 100 && (
                    <p className="text-xs text-gray-400 text-center py-3">
                      Showing 100 of {filtered?.length} records
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

          </div>
        </ScrollArea>
      </SidebarInset>
    </SidebarProvider>
  );
}
