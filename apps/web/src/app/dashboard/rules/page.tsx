"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, Rule } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import toast from "react-hot-toast";
import {
  ShieldCheckIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  BoltIcon,
  NoSymbolIcon,
  CheckBadgeIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";

const RULE_TYPES = [
  {
    id: "rate_limit",
    name: "Rate Limit",
    description: "Limit how many actions can be performed in a time window",
    icon: ClockIcon,
    color: "text-yellow-400 bg-yellow-400/10",
  },
  {
    id: "action_whitelist",
    name: "Action Whitelist",
    description: "Only allow specific actions",
    icon: CheckBadgeIcon,
    color: "text-green-400 bg-green-400/10",
  },
  {
    id: "action_blacklist",
    name: "Action Blacklist",
    description: "Block specific actions",
    icon: NoSymbolIcon,
    color: "text-red-400 bg-red-400/10",
  },
  {
    id: "require_approval",
    name: "Require Approval",
    description: "Require manual approval before executing",
    icon: ShieldCheckIcon,
    color: "text-purple-400 bg-purple-400/10",
  },
];

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [ruleType, setRuleType] = useState("rate_limit");
  const [maxRequests, setMaxRequests] = useState("100");
  const [windowSeconds, setWindowSeconds] = useState("3600");
  const [actions, setActions] = useState("");

  const loadRules = async () => {
    try {
      const data = await api.listRules();
      setRules(data);
    } catch {
      toast.error("Failed to load rules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const createRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);

    let config: Record<string, unknown> = {};
    if (ruleType === "rate_limit") {
      config = {
        max_requests: parseInt(maxRequests),
        window_seconds: parseInt(windowSeconds),
      };
    } else if (ruleType === "action_whitelist") {
      config = { allowed_actions: actions.split(",").map((a) => a.trim()) };
    } else if (ruleType === "action_blacklist") {
      config = { blocked_actions: actions.split(",").map((a) => a.trim()) };
    }

    try {
      await api.createRule({
        name,
        description: description || undefined,
        rule_type: ruleType,
        config,
      });
      toast.success("Rule created");
      setShowCreate(false);
      resetForm();
      loadRules();
    } catch (err: any) {
      toast.error(err.message || "Failed to create rule");
    } finally {
      setCreating(false);
    }
  };

  const deleteRule = async (ruleId: string, ruleName: string) => {
    if (!confirm(`Delete rule "${ruleName}"?`)) return;
    try {
      await api.deleteRule(ruleId);
      toast.success("Rule deleted");
      loadRules();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete rule");
    }
  };

  const toggleRule = async (rule: Rule) => {
    try {
      await api.updateRule(rule.id, { is_enabled: !rule.is_enabled });
      loadRules();
    } catch (err: any) {
      toast.error(err.message || "Failed to update rule");
    }
  };

  const resetForm = () => {
    setName("");
    setDescription("");
    setRuleType("rate_limit");
    setMaxRequests("100");
    setWindowSeconds("3600");
    setActions("");
  };

  const getRuleTypeInfo = (type: string) =>
    RULE_TYPES.find((t) => t.id === type);

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Rules</h1>
          <p className="mt-1 text-sm text-slate-400">
            Control what your AI agents can and cannot do
          </p>
        </div>
        <div className="flex gap-2">
          <a href="/dashboard/rules/templates" className="btn-secondary">
            Browse Templates
          </a>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <PlusIcon className="mr-2 h-4 w-4" />
            Create Rule
          </button>
        </div>
      </div>

      {/* Rule Type Cards */}
      <div className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {RULE_TYPES.map((type) => (
          <div
            key={type.id}
            className="card flex items-start gap-3 border-slate-700/50"
          >
            <div className={`rounded-lg p-2 ${type.color}`}>
              <type.icon className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">{type.name}</h3>
              <p className="text-xs text-slate-400">{type.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Rules List */}
      {rules.length > 0 ? (
        <div className="space-y-3">
          {rules.map((rule) => {
            const typeInfo = getRuleTypeInfo(rule.rule_type);
            return (
              <motion.div
                key={rule.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={`card flex items-center justify-between transition-opacity ${
                  !rule.is_enabled ? "opacity-50" : ""
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`rounded-xl p-3 ${typeInfo?.color || "bg-slate-700"}`}>
                    {typeInfo && <typeInfo.icon className="h-5 w-5" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-white">{rule.name}</p>
                      <span
                        className={`badge ${
                          rule.is_enabled ? "badge-success" : "badge-warning"
                        }`}
                      >
                        {rule.is_enabled ? "Active" : "Disabled"}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400">
                      {rule.description || typeInfo?.description}
                    </p>
                    <div className="mt-1 flex gap-2">
                      {rule.rule_type === "rate_limit" && (
                        <span className="text-xs text-slate-500">
                          {(rule.config as any).max_requests} requests /{" "}
                          {(rule.config as any).window_seconds}s
                        </span>
                      )}
                      {(rule.rule_type === "action_whitelist" ||
                        rule.rule_type === "action_blacklist") && (
                        <span className="text-xs text-slate-500">
                          {(
                            (rule.config as any).allowed_actions ||
                            (rule.config as any).blocked_actions ||
                            []
                          ).join(", ")}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggleRule(rule)}
                    className="btn-secondary px-3 py-1.5 text-xs"
                  >
                    {rule.is_enabled ? "Disable" : "Enable"}
                  </button>
                  <button
                    onClick={() => deleteRule(rule.id, rule.name)}
                    className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-400/10 hover:text-red-400"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        !loading && (
          <EmptyState
            icon={<ShieldCheckIcon className="h-8 w-8" />}
            title="No rules configured"
            description="Create rules to control rate limits, allowed actions, and approval workflows for your AI agents"
            action={
              <button onClick={() => setShowCreate(true)} className="btn-primary">
                <PlusIcon className="mr-2 h-4 w-4" />
                Create Your First Rule
              </button>
            }
          />
        )
      )}

      {/* Create Modal */}
      <Modal
        isOpen={showCreate}
        onClose={() => {
          setShowCreate(false);
          resetForm();
        }}
        title="Create Rule"
        size="lg"
      >
        <form onSubmit={createRule} className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Rule Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g., Gmail Send Rate Limit"
              required
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input"
              placeholder="Optional description"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Rule Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {RULE_TYPES.map((type) => (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => setRuleType(type.id)}
                  className={`flex items-center gap-2 rounded-lg border p-3 text-left text-sm transition-all ${
                    ruleType === type.id
                      ? "border-brand-500 bg-brand-500/10 text-brand-400"
                      : "border-slate-600 text-slate-400 hover:border-slate-500"
                  }`}
                >
                  <type.icon className="h-4 w-4" />
                  {type.name}
                </button>
              ))}
            </div>
          </div>

          {ruleType === "rate_limit" && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-300">
                  Max Requests
                </label>
                <input
                  type="number"
                  value={maxRequests}
                  onChange={(e) => setMaxRequests(e.target.value)}
                  className="input"
                  min="1"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-300">
                  Time Window (seconds)
                </label>
                <input
                  type="number"
                  value={windowSeconds}
                  onChange={(e) => setWindowSeconds(e.target.value)}
                  className="input"
                  min="1"
                />
              </div>
            </div>
          )}

          {(ruleType === "action_whitelist" ||
            ruleType === "action_blacklist") && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                Actions (comma-separated)
              </label>
              <input
                type="text"
                value={actions}
                onChange={(e) => setActions(e.target.value)}
                className="input"
                placeholder="gmail.send, gmail.read, calendar.create"
              />
              <p className="mt-1 text-xs text-slate-500">
                Format: service.action (e.g., gmail.send, calendar.list,
                drive.read)
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setShowCreate(false);
                resetForm();
              }}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={creating || !name}
            >
              {creating ? "Creating..." : "Create Rule"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
