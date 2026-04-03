"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, ApiKey } from "@/lib/api";
import { formatDate, timeAgo } from "@/lib/utils";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import toast from "react-hot-toast";
import {
  KeyIcon,
  PlusIcon,
  TrashIcon,
  ClipboardDocumentIcon,
  CheckIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

export default function KeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Form
  const [name, setName] = useState("");
  const [providers, setProviders] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);

  const loadKeys = async () => {
    try {
      const data = await api.listApiKeys();
      setKeys(data);
    } catch {
      toast.error("Failed to load API keys");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const createKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const data = await api.createApiKey({
        name,
        allowed_providers: providers.length > 0 ? providers : undefined,
      });
      setNewKey(data.key!);
      setName("");
      setProviders([]);
      loadKeys();
    } catch (err: any) {
      toast.error(err.message || "Failed to create API key");
    } finally {
      setCreating(false);
    }
  };

  const revokeKey = async (keyId: string, keyName: string) => {
    if (!confirm(`Revoke API key "${keyName}"? This cannot be undone.`)) return;
    try {
      await api.revokeApiKey(keyId);
      toast.success("API key revoked");
      loadKeys();
    } catch (err: any) {
      toast.error(err.message || "Failed to revoke key");
    }
  };

  const copyKey = async () => {
    if (!newKey) return;
    await navigator.clipboard.writeText(newKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const activeKeys = keys.filter((k) => !k.revoked_at);
  const revokedKeys = keys.filter((k) => k.revoked_at);

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">API Keys</h1>
          <p className="mt-1 text-sm text-slate-400">
            Create and manage API keys for your AI agents
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <PlusIcon className="mr-2 h-4 w-4" />
          Create Key
        </button>
      </div>

      {/* New Key Display */}
      <AnimatePresence>
        {newKey && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-6 rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-6"
          >
            <div className="mb-3 flex items-center gap-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
              <h3 className="font-semibold text-yellow-300">
                Save your API key now
              </h3>
            </div>
            <p className="mb-4 text-sm text-yellow-200/70">
              This key will only be shown once. Copy it and store it securely.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 rounded-lg bg-slate-800 px-4 py-3 font-mono text-sm text-green-400 select-all">
                {newKey}
              </code>
              <button
                onClick={copyKey}
                className="rounded-lg bg-slate-700 p-3 text-slate-300 transition-colors hover:bg-slate-600"
              >
                {copied ? (
                  <CheckIcon className="h-5 w-5 text-green-400" />
                ) : (
                  <ClipboardDocumentIcon className="h-5 w-5" />
                )}
              </button>
            </div>
            <button
              onClick={() => setNewKey(null)}
              className="mt-3 text-sm text-slate-400 hover:text-slate-300"
            >
              I&apos;ve saved it, dismiss
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Active Keys */}
      {activeKeys.length > 0 ? (
        <div className="space-y-3">
          {activeKeys.map((key) => (
            <motion.div
              key={key.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="card flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="rounded-xl bg-emerald-400/10 p-3">
                  <KeyIcon className="h-5 w-5 text-emerald-400" />
                </div>
                <div>
                  <p className="font-medium text-white">{key.name}</p>
                  <div className="flex items-center gap-3 text-sm text-slate-400">
                    <code className="rounded bg-slate-700/50 px-1.5 py-0.5 text-xs">
                      {key.key_prefix}...
                    </code>
                    <span>Created {formatDate(key.created_at)}</span>
                    {key.last_used_at && (
                      <span>Last used {timeAgo(key.last_used_at)}</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {key.allowed_providers && key.allowed_providers.length > 0 && (
                  <div className="flex gap-1">
                    {key.allowed_providers.map((p) => (
                      <span key={p} className="badge-info">
                        {p}
                      </span>
                    ))}
                  </div>
                )}
                <button
                  onClick={() => revokeKey(key.id, key.name)}
                  className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-400/10 hover:text-red-400"
                  title="Revoke"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        !loading && (
          <EmptyState
            icon={<KeyIcon className="h-8 w-8" />}
            title="No API keys yet"
            description="Create an API key to let your AI agents access connected accounts through the gateway"
            action={
              <button onClick={() => setShowCreate(true)} className="btn-primary">
                <PlusIcon className="mr-2 h-4 w-4" />
                Create Your First Key
              </button>
            }
          />
        )
      )}

      {/* Revoked Keys */}
      {revokedKeys.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
            Revoked Keys
          </h2>
          <div className="space-y-2">
            {revokedKeys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between rounded-xl border border-slate-700/50 bg-slate-800/30 px-6 py-4 opacity-60"
              >
                <div className="flex items-center gap-4">
                  <KeyIcon className="h-5 w-5 text-slate-600" />
                  <div>
                    <p className="font-medium text-slate-400 line-through">
                      {key.name}
                    </p>
                    <p className="text-xs text-slate-600">
                      Revoked {key.revoked_at && formatDate(key.revoked_at)}
                    </p>
                  </div>
                </div>
                <span className="badge-danger">Revoked</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="Create API Key"
      >
        <form onSubmit={createKey} className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Key Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g., My Agent, Production Bot"
              required
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Allowed Providers
              <span className="ml-1 text-xs text-slate-500">(optional)</span>
            </label>
            <div className="flex gap-2">
              {["google"].map((provider) => (
                <button
                  key={provider}
                  type="button"
                  onClick={() =>
                    setProviders((prev) =>
                      prev.includes(provider)
                        ? prev.filter((p) => p !== provider)
                        : [...prev, provider]
                    )
                  }
                  className={`rounded-lg border px-3 py-2 text-sm transition-all ${
                    providers.includes(provider)
                      ? "border-brand-500 bg-brand-500/10 text-brand-400"
                      : "border-slate-600 text-slate-400 hover:border-slate-500"
                  }`}
                >
                  {provider.charAt(0).toUpperCase() + provider.slice(1)}
                </button>
              ))}
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Leave empty to allow all providers
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={creating || !name}
            >
              {creating ? "Creating..." : "Create Key"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
