"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, timeAgo } from "@/lib/utils";
import toast from "react-hot-toast";
import Link from "next/link";
import {
  UsersIcon,
  BoltIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getAgentsOverview()
      .then((data) => setAgents(data.agents || []))
      .catch(() => toast.error("Failed to load agents"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Agents</h1>
        <p className="mt-1 text-sm text-slate-400">
          Monitor all your AI agents and their activity at a glance
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl bg-slate-800/50" />
          ))}
        </div>
      ) : agents.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent, i) => (
            <motion.div
              key={agent.key_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="card"
            >
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`rounded-xl p-2.5 ${
                      agent.is_active
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-red-500/10 text-red-400"
                    }`}
                  >
                    <BoltIcon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{agent.name}</h3>
                    <p className="text-xs text-slate-500">
                      {agent.key_prefix}...
                    </p>
                  </div>
                </div>
                <span
                  className={
                    agent.is_active ? "badge-success" : "badge-danger"
                  }
                >
                  {agent.is_active ? "Active" : "Revoked"}
                </span>
              </div>

              {/* 24h Stats */}
              <div className="mb-4 grid grid-cols-3 gap-2">
                <div className="rounded-lg bg-slate-700/30 px-3 py-2 text-center">
                  <p className="text-lg font-bold text-white">
                    {agent.stats_24h?.total_actions || 0}
                  </p>
                  <p className="text-xs text-slate-500">Actions</p>
                </div>
                <div className="rounded-lg bg-slate-700/30 px-3 py-2 text-center">
                  <p className="text-lg font-bold text-green-400">
                    {agent.stats_24h?.successful || 0}
                  </p>
                  <p className="text-xs text-slate-500">Success</p>
                </div>
                <div className="rounded-lg bg-slate-700/30 px-3 py-2 text-center">
                  <p className="text-lg font-bold text-red-400">
                    {agent.stats_24h?.denied || 0}
                  </p>
                  <p className="text-xs text-slate-500">Denied</p>
                </div>
              </div>

              {/* Top Actions */}
              {agent.stats_24h?.top_actions &&
                agent.stats_24h.top_actions.length > 0 && (
                  <div className="mb-3">
                    <p className="mb-1 text-xs text-slate-500">Top actions</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.stats_24h.top_actions
                        .slice(0, 3)
                        .map((a: any) => (
                          <span
                            key={a.action}
                            className="rounded-full bg-slate-700/50 px-2 py-0.5 text-xs text-slate-400"
                          >
                            {a.action} ({a.count})
                          </span>
                        ))}
                    </div>
                  </div>
                )}

              <div className="flex items-center gap-1 text-xs text-slate-500">
                <ClockIcon className="h-3 w-3" />
                {agent.last_used_at
                  ? `Last active ${timeAgo(agent.last_used_at)}`
                  : "Never used"}
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<UsersIcon className="h-8 w-8" />}
          title="No agents yet"
          description="Create API keys in the API Keys page to register agents"
          action={
            <Link href="/dashboard/keys" className="btn-primary">
              Go to API Keys
            </Link>
          }
        />
      )}
    </div>
  );
}
