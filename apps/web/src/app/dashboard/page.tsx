"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, ConnectedAccount, ApiKey, AuditLog } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { formatDate, timeAgo } from "@/lib/utils";
import {
  LinkIcon,
  KeyIcon,
  ShieldCheckIcon,
  ClipboardDocumentListIcon,
  ArrowTrendingUpIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";

const fadeIn = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.listAccounts().catch(() => []),
      api.listApiKeys().catch(() => []),
      api.listAuditLogs({ limit: 5 }).catch(() => []),
    ]).then(([a, k, l]) => {
      setAccounts(a);
      setApiKeys(k);
      setRecentLogs(l);
      setLoading(false);
    });
  }, []);

  const activeKeys = apiKeys.filter((k) => !k.revoked_at);

  const stats = [
    {
      name: "Connected Accounts",
      value: accounts.length,
      icon: LinkIcon,
      href: "/dashboard/accounts",
      color: "text-blue-400",
      bg: "bg-blue-400/10",
    },
    {
      name: "Active API Keys",
      value: activeKeys.length,
      icon: KeyIcon,
      href: "/dashboard/keys",
      color: "text-emerald-400",
      bg: "bg-emerald-400/10",
    },
    {
      name: "Recent Actions",
      value: recentLogs.length,
      icon: ArrowTrendingUpIcon,
      href: "/dashboard/audit",
      color: "text-purple-400",
      bg: "bg-purple-400/10",
    },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back{user?.display_name ? `, ${user.display_name}` : ""}
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Manage your connected accounts, API keys, and security rules
        </p>
      </div>

      {/* Stats */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.name}
            {...fadeIn}
            transition={{ delay: i * 0.1 }}
          >
            <Link href={stat.href} className="card group block transition-all hover:border-slate-600">
              <div className="flex items-center gap-4">
                <div className={`rounded-xl ${stat.bg} p-3`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div>
                  <p className="text-sm text-slate-400">{stat.name}</p>
                  <p className="text-2xl font-bold text-white">
                    {loading ? "-" : stat.value}
                  </p>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Recent Activity */}
      <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">
              Recent Activity
            </h2>
            <Link
              href="/dashboard/audit"
              className="text-sm text-brand-400 hover:text-brand-300"
            >
              View all
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-slate-700/50" />
              ))}
            </div>
          ) : recentLogs.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-500">
              No activity yet. Connect an account to get started.
            </p>
          ) : (
            <div className="space-y-2">
              {recentLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/50 px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        log.status === "success"
                          ? "bg-green-400"
                          : log.status === "denied"
                          ? "bg-red-400"
                          : "bg-yellow-400"
                      }`}
                    />
                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        {log.action}
                      </p>
                      {log.detail && (
                        <p className="text-xs text-slate-500">{log.detail}</p>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-slate-500">
                    {timeAgo(log.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
