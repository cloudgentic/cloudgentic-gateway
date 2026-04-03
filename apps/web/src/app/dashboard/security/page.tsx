"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import { formatDate, timeAgo } from "@/lib/utils";
import toast from "react-hot-toast";
import {
  ShieldExclamationIcon,
  BoltIcon,
  ExclamationTriangleIcon,
  BeakerIcon,
  BugAntIcon,
  CheckCircleIcon,
  XCircleIcon,
  StopIcon,
} from "@heroicons/react/24/outline";

interface KillSwitchStatus {
  is_active: boolean;
  activated_at: string | null;
  trigger_source: string | null;
  keys_revoked: number;
  tokens_revoked: number;
}

interface AnomalyEvent {
  id: string;
  anomaly_type: string;
  severity: string;
  details: Record<string, unknown>;
  auto_action_taken: string | null;
  acknowledged_at: string | null;
  created_at: string;
}

interface ScanResult {
  risk_score: number;
  risk_level: string;
  concerns: {
    severity: string;
    category: string;
    description: string;
    evidence: string | null;
    line_number: number | null;
  }[];
  recommendations: string[];
}

const SEVERITY_COLORS: Record<string, string> = {
  low: "bg-blue-400/10 text-blue-400 border-blue-400/20",
  medium: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20",
  high: "bg-orange-400/10 text-orange-400 border-orange-400/20",
  critical: "bg-red-400/10 text-red-400 border-red-400/20",
};

const RISK_COLORS: Record<string, string> = {
  safe: "text-green-400",
  low: "text-blue-400",
  medium: "text-yellow-400",
  high: "text-orange-400",
  critical: "text-red-400",
};

export default function SecurityPage() {
  const [killStatus, setKillStatus] = useState<KillSwitchStatus | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyEvent[]>([]);
  const [showKillConfirm, setShowKillConfirm] = useState(false);
  const [killReason, setKillReason] = useState("");
  const [disconnectAccounts, setDisconnectAccounts] = useState(false);
  const [executing, setExecuting] = useState(false);

  // Skill Scanner
  const [showScanner, setShowScanner] = useState(false);
  const [skillName, setSkillName] = useState("");
  const [skillContent, setSkillContent] = useState("");
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);

  const loadData = async () => {
    try {
      const [ks, an] = await Promise.all([
        api.getKillSwitchStatus().catch(() => null),
        api.listAnomalies().catch(() => []),
      ]);
      if (ks) setKillStatus(ks);
      setAnomalies(an);
    } catch {}
  };

  useEffect(() => {
    loadData();
  }, []);

  const activateKillSwitch = async () => {
    setExecuting(true);
    try {
      await api.activateKillSwitch({
        revoke_api_keys: true,
        disconnect_accounts: disconnectAccounts,
        reason: killReason || undefined,
      });
      toast.success("Kill switch activated — all agent access revoked");
      setShowKillConfirm(false);
      setKillReason("");
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to activate kill switch");
    } finally {
      setExecuting(false);
    }
  };

  const scanSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    setScanning(true);
    setScanResult(null);
    try {
      const result = await api.scanSkill({
        skill_name: skillName,
        skill_md_content: skillContent || undefined,
      });
      setScanResult(result);
    } catch (err: any) {
      toast.error(err.message || "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  const acknowledgeAnomaly = async (id: string) => {
    try {
      await api.acknowledgeAnomaly(id);
      loadData();
    } catch {}
  };

  const unacknowledgedCount = anomalies.filter(
    (a) => !a.acknowledged_at
  ).length;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Security</h1>
        <p className="mt-1 text-sm text-slate-400">
          Emergency controls, anomaly detection, and skill scanning
        </p>
      </div>

      <div className="max-w-3xl space-y-6">
        {/* Kill Switch */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-2xl border p-6 ${
            killStatus?.is_active
              ? "border-red-500/50 bg-red-500/5"
              : "border-slate-700 bg-slate-800"
          }`}
        >
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-red-500/10 p-3">
                <StopIcon className="h-6 w-6 text-red-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">
                  Emergency Kill Switch
                </h2>
                <p className="text-sm text-slate-400">
                  Instantly revoke all agent access
                </p>
              </div>
            </div>
            {killStatus?.is_active && (
              <span className="badge-danger flex items-center gap-1 px-3 py-1">
                <BoltIcon className="h-3.5 w-3.5" />
                ACTIVE
              </span>
            )}
          </div>

          {killStatus?.is_active ? (
            <div className="rounded-xl bg-red-500/10 p-4">
              <p className="text-sm text-red-300">
                Kill switch activated{" "}
                {killStatus.activated_at && timeAgo(killStatus.activated_at)} via{" "}
                {killStatus.trigger_source}.{" "}
                {killStatus.keys_revoked} keys revoked
                {killStatus.tokens_revoked > 0 &&
                  `, ${killStatus.tokens_revoked} accounts disconnected`}
                .
              </p>
              <p className="mt-2 text-xs text-red-400/60">
                Create new API keys to re-enable agent access.
              </p>
            </div>
          ) : (
            <button
              onClick={() => setShowKillConfirm(true)}
              className="w-full rounded-xl bg-red-600 px-6 py-4 text-lg font-bold text-white shadow-lg shadow-red-600/20 transition-all hover:bg-red-700 hover:shadow-red-600/30 active:scale-[0.98]"
            >
              Emergency Stop — Revoke All Agent Access
            </button>
          )}
        </motion.div>

        {/* Anomalies */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-yellow-500/10 p-2.5">
                <ShieldExclamationIcon className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <h2 className="font-semibold text-white">
                  Anomaly Detection
                  {unacknowledgedCount > 0 && (
                    <span className="ml-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
                      {unacknowledgedCount}
                    </span>
                  )}
                </h2>
                <p className="text-xs text-slate-400">
                  Unusual agent behavior alerts
                </p>
              </div>
            </div>
          </div>

          {anomalies.length > 0 ? (
            <div className="space-y-2">
              {anomalies.slice(0, 10).map((a) => (
                <div
                  key={a.id}
                  className={`flex items-center justify-between rounded-lg border px-4 py-3 ${
                    a.acknowledged_at
                      ? "border-slate-700/30 bg-slate-800/30 opacity-50"
                      : SEVERITY_COLORS[a.severity] || SEVERITY_COLORS.medium
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`badge ${
                          SEVERITY_COLORS[a.severity] || ""
                        } border`}
                      >
                        {a.severity}
                      </span>
                      <span className="text-sm font-medium text-white">
                        {a.anomaly_type.replace("_", " ")}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">
                      {(a.details as any).action || (a.details as any).message || JSON.stringify(a.details).slice(0, 100)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">
                      {timeAgo(a.created_at)}
                    </span>
                    {!a.acknowledged_at && (
                      <button
                        onClick={() => acknowledgeAnomaly(a.id)}
                        className="rounded-lg px-2 py-1 text-xs text-slate-400 hover:bg-slate-700"
                      >
                        Dismiss
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="py-6 text-center text-sm text-slate-500">
              No anomalies detected. Your agents are behaving normally.
            </p>
          )}
        </motion.div>

        {/* Skill Scanner */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-xl bg-purple-500/10 p-2.5">
              <BugAntIcon className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h2 className="font-semibold text-white">Skill Security Scanner</h2>
              <p className="text-xs text-slate-400">
                Scan OpenClaw skills for malware before installing
              </p>
            </div>
          </div>

          <form onSubmit={scanSkill} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                Skill Name
              </label>
              <input
                type="text"
                value={skillName}
                onChange={(e) => setSkillName(e.target.value)}
                className="input"
                placeholder="e.g., solana-wallet-tracker"
                required
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                SKILL.md or Code Content
                <span className="ml-1 text-xs text-slate-500">(paste the skill's code here)</span>
              </label>
              <textarea
                value={skillContent}
                onChange={(e) => setSkillContent(e.target.value)}
                className="input min-h-[120px] font-mono text-xs"
                placeholder="Paste SKILL.md or code content to scan..."
              />
            </div>
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={scanning || !skillName}
            >
              {scanning ? "Scanning..." : "Scan Skill"}
            </button>
          </form>

          {/* Scan Results */}
          <AnimatePresence>
            {scanResult && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4"
              >
                <div
                  className={`rounded-xl border p-4 ${
                    scanResult.risk_level === "safe"
                      ? "border-green-500/30 bg-green-500/5"
                      : scanResult.risk_level === "critical"
                      ? "border-red-500/30 bg-red-500/5"
                      : "border-yellow-500/30 bg-yellow-500/5"
                  }`}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {scanResult.risk_level === "safe" ? (
                        <CheckCircleIcon className="h-5 w-5 text-green-400" />
                      ) : (
                        <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                      )}
                      <span
                        className={`text-lg font-bold ${
                          RISK_COLORS[scanResult.risk_level] || ""
                        }`}
                      >
                        {scanResult.risk_level.toUpperCase()}
                      </span>
                    </div>
                    <span className="text-sm text-slate-400">
                      Score: {scanResult.risk_score}/100
                    </span>
                  </div>

                  {scanResult.concerns.length > 0 && (
                    <div className="mb-3 space-y-2">
                      {scanResult.concerns.map((c, i) => (
                        <div
                          key={i}
                          className="rounded-lg bg-slate-800/50 px-3 py-2"
                        >
                          <div className="flex items-center gap-2">
                            <span
                              className={`badge border text-xs ${
                                SEVERITY_COLORS[c.severity] || ""
                              }`}
                            >
                              {c.severity}
                            </span>
                            <span className="text-xs text-slate-500">
                              {c.category}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-slate-300">
                            {c.description}
                          </p>
                          {c.evidence && (
                            <code className="mt-1 block truncate text-xs text-slate-500">
                              {c.evidence}
                            </code>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="space-y-1">
                    {scanResult.recommendations.map((r, i) => (
                      <p key={i} className="text-sm text-slate-400">
                        {r}
                      </p>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Kill Switch Confirmation Modal */}
      <Modal
        isOpen={showKillConfirm}
        onClose={() => setShowKillConfirm(false)}
        title="Activate Emergency Kill Switch"
      >
        <div className="space-y-4">
          <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4">
            <p className="text-sm text-red-300">
              This will immediately revoke ALL agent API keys. Agents will lose
              access to all connected accounts. You will need to create new API
              keys to re-enable agents.
            </p>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Reason (optional)
            </label>
            <input
              type="text"
              value={killReason}
              onChange={(e) => setKillReason(e.target.value)}
              className="input"
              placeholder="e.g., Agent sending unauthorized emails"
            />
          </div>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={disconnectAccounts}
              onChange={(e) => setDisconnectAccounts(e.target.checked)}
              className="rounded border-slate-600 bg-slate-700"
            />
            <span className="text-sm text-slate-300">
              Also disconnect all OAuth accounts (revoke tokens)
            </span>
          </label>

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => setShowKillConfirm(false)}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              onClick={activateKillSwitch}
              className="btn-danger flex-1"
              disabled={executing}
            >
              {executing ? "Executing..." : "Activate Kill Switch"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
