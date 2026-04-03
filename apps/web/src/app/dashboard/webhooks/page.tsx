"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, timeAgo } from "@/lib/utils";
import toast from "react-hot-toast";
import {
  RssIcon,
  PlusIcon,
  TrashIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline";

const EVENT_TYPES = [
  "action.success",
  "action.denied",
  "action.error",
  "anomaly.detected",
  "kill_switch.activated",
];

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [events, setEvents] = useState<Record<string, any[]>>({});

  // Form
  const [eventType, setEventType] = useState("action.success");
  const [callbackUrl, setCallbackUrl] = useState("");
  const [creating, setCreating] = useState(false);

  const loadWebhooks = async () => {
    try {
      const data = await api.listWebhooks();
      setWebhooks(data);
    } catch {
      toast.error("Failed to load webhooks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWebhooks();
  }, []);

  const createWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.createWebhook({ event_type: eventType, callback_url: callbackUrl });
      toast.success("Webhook created");
      setShowCreate(false);
      setCallbackUrl("");
      loadWebhooks();
    } catch (err: any) {
      toast.error(err.message || "Failed to create webhook");
    } finally {
      setCreating(false);
    }
  };

  const deleteWebhook = async (id: string) => {
    if (!confirm("Deactivate this webhook?")) return;
    try {
      await api.deleteWebhook(id);
      toast.success("Webhook deactivated");
      loadWebhooks();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete");
    }
  };

  const toggleEvents = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!events[id]) {
      try {
        const data = await api.listWebhookEvents(id);
        setEvents((prev) => ({ ...prev, [id]: data }));
      } catch {}
    }
  };

  const activeWebhooks = webhooks.filter((w) => w.is_active);

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Webhooks</h1>
          <p className="mt-1 text-sm text-slate-400">
            Subscribe to gateway events and receive notifications at your endpoints
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <PlusIcon className="mr-2 h-4 w-4" />
          Create Webhook
        </button>
      </div>

      {activeWebhooks.length > 0 ? (
        <div className="space-y-3">
          {activeWebhooks.map((wh) => (
            <motion.div
              key={wh.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="card"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="rounded-xl bg-brand-600/10 p-3">
                    <RssIcon className="h-5 w-5 text-brand-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="badge-info">{wh.event_type}</span>
                      <span className="badge-success">Active</span>
                    </div>
                    <p className="mt-1 text-sm text-slate-400">
                      {wh.callback_url}
                    </p>
                    <p className="text-xs text-slate-500">
                      Created {formatDate(wh.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggleEvents(wh.id)}
                    className="btn-secondary px-3 py-1.5 text-xs"
                  >
                    Events
                    <ChevronDownIcon
                      className={`ml-1 h-3 w-3 transition-transform ${
                        expandedId === wh.id ? "rotate-180" : ""
                      }`}
                    />
                  </button>
                  <button
                    onClick={() => deleteWebhook(wh.id)}
                    className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-400/10 hover:text-red-400"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {expandedId === wh.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="mt-4 border-t border-slate-700 pt-4"
                >
                  {(events[wh.id] || []).length > 0 ? (
                    <div className="space-y-2">
                      {events[wh.id].slice(0, 10).map((ev: any) => (
                        <div
                          key={ev.id}
                          className="flex items-center justify-between rounded-lg bg-slate-700/30 px-3 py-2"
                        >
                          <div className="flex items-center gap-2">
                            <span
                              className={`h-2 w-2 rounded-full ${
                                ev.delivery_status === "delivered"
                                  ? "bg-green-400"
                                  : ev.delivery_status === "failed"
                                  ? "bg-red-400"
                                  : "bg-yellow-400"
                              }`}
                            />
                            <span className="text-sm text-slate-300">
                              {ev.event_type}
                            </span>
                            <span className="text-xs text-slate-500">
                              {ev.delivery_status}
                            </span>
                          </div>
                          <span className="text-xs text-slate-500">
                            {timeAgo(ev.created_at)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-sm text-slate-500">
                      No events yet
                    </p>
                  )}
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      ) : (
        !loading && (
          <EmptyState
            icon={<RssIcon className="h-8 w-8" />}
            title="No webhooks configured"
            description="Create a webhook to receive real-time notifications when events occur in the gateway"
            action={
              <button onClick={() => setShowCreate(true)} className="btn-primary">
                <PlusIcon className="mr-2 h-4 w-4" />
                Create Webhook
              </button>
            }
          />
        )
      )}

      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="Create Webhook"
      >
        <form onSubmit={createWebhook} className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Event Type
            </label>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="input"
            >
              {EVENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Callback URL
            </label>
            <input
              type="url"
              value={callbackUrl}
              onChange={(e) => setCallbackUrl(e.target.value)}
              className="input"
              placeholder="https://your-server.com/webhook"
              required
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" className="btn-primary flex-1" disabled={creating || !callbackUrl}>
              {creating ? "Creating..." : "Create Webhook"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
