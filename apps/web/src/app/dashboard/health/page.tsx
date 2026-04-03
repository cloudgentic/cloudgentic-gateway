"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, timeAgo } from "@/lib/utils";
import toast from "react-hot-toast";
import {
  HeartIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";

const TOKEN_STATUS_CONFIG: Record<string, { color: string; label: string; icon: any }> = {
  valid: { color: "text-green-400", label: "Valid", icon: CheckCircleIcon },
  expiring_soon: { color: "text-yellow-400", label: "Expiring Soon", icon: ExclamationTriangleIcon },
  expired: { color: "text-red-400", label: "Expired", icon: XCircleIcon },
  missing: { color: "text-slate-500", label: "Missing", icon: XCircleIcon },
};

const OVERALL_STATUS_CONFIG: Record<string, { color: string; bg: string }> = {
  healthy: { color: "text-green-400", bg: "bg-green-500/10" },
  degraded: { color: "text-yellow-400", bg: "bg-yellow-500/10" },
  critical: { color: "text-red-400", bg: "bg-red-500/10" },
};

export default function HealthPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadHealth = async () => {
    setLoading(true);
    try {
      const data = await api.getProviderHealth();
      setHealth(data);
    } catch {
      toast.error("Failed to load health data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const overall = health?.overall_status || "healthy";
  const overallConfig = OVERALL_STATUS_CONFIG[overall] || OVERALL_STATUS_CONFIG.healthy;
  const providers = health?.providers || [];

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Provider Health</h1>
          <p className="mt-1 text-sm text-slate-400">
            Token status, rate limits, and API availability for connected accounts
          </p>
        </div>
        <button onClick={loadHealth} className="btn-secondary">
          <ArrowPathIcon className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Overall Status */}
      {health && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mb-8 rounded-2xl border border-slate-700 ${overallConfig.bg} p-6`}
        >
          <div className="flex items-center gap-3">
            <HeartIcon className={`h-8 w-8 ${overallConfig.color}`} />
            <div>
              <h2 className={`text-xl font-bold ${overallConfig.color}`}>
                {overall.charAt(0).toUpperCase() + overall.slice(1)}
              </h2>
              <p className="text-sm text-slate-400">
                {providers.length} connected account{providers.length !== 1 ? "s" : ""} monitored
                {health.checked_at && ` — last checked ${timeAgo(health.checked_at)}`}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Provider Cards */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-slate-800/50" />
          ))}
        </div>
      ) : providers.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {providers.map((p: any, i: number) => {
            const tokenConfig = TOKEN_STATUS_CONFIG[p.token_status] || TOKEN_STATUS_CONFIG.missing;
            const TokenIcon = tokenConfig.icon;

            return (
              <motion.div
                key={p.account_id || i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="card"
              >
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-white">
                      {p.provider?.charAt(0).toUpperCase() + p.provider?.slice(1)}
                    </h3>
                    <p className="text-sm text-slate-400">
                      {p.account_label || p.account_id}
                    </p>
                  </div>
                  <div className={`flex items-center gap-1 ${tokenConfig.color}`}>
                    <TokenIcon className="h-4 w-4" />
                    <span className="text-sm font-medium">{tokenConfig.label}</span>
                  </div>
                </div>

                {/* Token Expiry */}
                {p.token_expires_in_seconds != null && (
                  <div className="mb-3">
                    <div className="mb-1 flex justify-between text-xs text-slate-500">
                      <span>Token expires</span>
                      <span>
                        {p.token_expires_in_seconds > 3600
                          ? `${Math.floor(p.token_expires_in_seconds / 3600)}h`
                          : `${Math.floor(p.token_expires_in_seconds / 60)}m`}
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-slate-700">
                      <div
                        className={`h-full rounded-full ${
                          p.token_expires_in_seconds > 1800
                            ? "bg-green-500"
                            : p.token_expires_in_seconds > 300
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                        style={{
                          width: `${Math.min(
                            (p.token_expires_in_seconds / 3600) * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Rate Limit */}
                {p.rate_limit && p.rate_limit.daily_limit && (
                  <div className="mb-3">
                    <div className="mb-1 flex justify-between text-xs text-slate-500">
                      <span>Daily rate limit</span>
                      <span>
                        {p.rate_limit.daily_used}/{p.rate_limit.daily_limit}
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-slate-700">
                      <div
                        className={`h-full rounded-full ${
                          p.rate_limit.daily_used / p.rate_limit.daily_limit < 0.7
                            ? "bg-brand-500"
                            : p.rate_limit.daily_used / p.rate_limit.daily_limit < 0.9
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                        style={{
                          width: `${Math.min(
                            (p.rate_limit.daily_used / p.rate_limit.daily_limit) * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Last Action */}
                {p.last_successful_action && (
                  <p className="text-xs text-slate-500">
                    Last action: {p.last_successful_action.action}{" "}
                    {p.last_successful_action.at && timeAgo(p.last_successful_action.at)}
                  </p>
                )}
              </motion.div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={<HeartIcon className="h-8 w-8" />}
          title="No connected accounts"
          description="Connect an account to monitor its health"
        />
      )}
    </div>
  );
}
