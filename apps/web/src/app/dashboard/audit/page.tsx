"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, AuditLog } from "@/lib/api";
import { formatDate, cn } from "@/lib/utils";
import { EmptyState } from "@/components/ui/EmptyState";
import toast from "react-hot-toast";
import {
  ClipboardDocumentListIcon,
  FunnelIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";

const STATUS_STYLES: Record<string, string> = {
  success: "bg-green-400/10 text-green-400 border-green-400/20",
  denied: "bg-red-400/10 text-red-400 border-red-400/20",
  error: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20",
};

const ACTION_COLORS: Record<string, string> = {
  "auth.": "text-blue-400",
  "account.": "text-purple-400",
  "api_key.": "text-emerald-400",
  "rule.": "text-yellow-400",
  "gmail.": "text-red-400",
  "calendar.": "text-cyan-400",
  "drive.": "text-orange-400",
};

function getActionColor(action: string): string {
  for (const [prefix, color] of Object.entries(ACTION_COLORS)) {
    if (action.startsWith(prefix)) return color;
  }
  return "text-slate-300";
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    action: "",
    provider: "",
    status: "",
  });
  const [limit, setLimit] = useState(50);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { limit };
      if (filter.action) params.action = filter.action;
      if (filter.provider) params.provider = filter.provider;
      if (filter.status) params.status = filter.status;
      const data = await api.listAuditLogs(params);
      setLogs(data);
    } catch {
      toast.error("Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [filter, limit]);

  const uniqueActions = [...new Set(logs.map((l) => l.action))].sort();
  const uniqueProviders = [
    ...new Set(logs.filter((l) => l.provider).map((l) => l.provider!)),
  ].sort();

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Log</h1>
          <p className="mt-1 text-sm text-slate-400">
            Complete history of all actions performed through the gateway
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={async () => {
              try {
                const blob = await api.exportAuditLogs({
                  status: filter.status || undefined,
                  provider: filter.provider || undefined,
                  limit: 10000,
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `audit_export_${new Date().toISOString().slice(0, 10)}.csv`;
                a.click();
                URL.revokeObjectURL(url);
              } catch {
                toast.error("Export failed");
              }
            }}
            className="btn-secondary"
          >
            Export CSV
          </button>
          <button onClick={loadLogs} className="btn-secondary">
            <ArrowPathIcon className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <FunnelIcon className="h-4 w-4 text-slate-500" />
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="input w-auto"
        >
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="denied">Denied</option>
          <option value="error">Error</option>
        </select>
        <select
          value={filter.provider}
          onChange={(e) => setFilter({ ...filter, provider: e.target.value })}
          className="input w-auto"
        >
          <option value="">All providers</option>
          {uniqueProviders.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select
          value={String(limit)}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="input w-auto"
        >
          <option value="25">25 entries</option>
          <option value="50">50 entries</option>
          <option value="100">100 entries</option>
          <option value="200">200 entries</option>
        </select>
      </div>

      {/* Logs Table */}
      {logs.length > 0 ? (
        <div className="overflow-hidden rounded-xl border border-slate-700">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-800/80">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Time
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Provider
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Detail
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {logs.map((log, i) => (
                <motion.tr
                  key={log.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                  className="bg-slate-800/30 transition-colors hover:bg-slate-800/60"
                >
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-400">
                    {formatDate(log.timestamp)}
                  </td>
                  <td className="px-4 py-3">
                    <code
                      className={cn(
                        "text-sm font-medium",
                        getActionColor(log.action)
                      )}
                    >
                      {log.action}
                    </code>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {log.provider || "-"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
                        STATUS_STYLES[log.status] || STATUS_STYLES.error
                      )}
                    >
                      {log.status}
                    </span>
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-sm text-slate-500">
                    {log.detail || "-"}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        !loading && (
          <EmptyState
            icon={<ClipboardDocumentListIcon className="h-8 w-8" />}
            title="No audit logs yet"
            description="Actions performed through the gateway will appear here"
          />
        )
      )}

      {loading && (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="h-14 animate-pulse rounded-lg bg-slate-800/50"
            />
          ))}
        </div>
      )}
    </div>
  );
}
