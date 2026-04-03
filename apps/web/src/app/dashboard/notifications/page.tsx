"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import {
  BellIcon,
  EnvelopeIcon,
  CheckCircleIcon,
  PaperAirplaneIcon,
  RssIcon,
} from "@heroicons/react/24/outline";

export default function NotificationsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);

  // Form state
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [emailAddress, setEmailAddress] = useState("");
  const [telegramEnabled, setTelegramEnabled] = useState(false);
  const [telegramChatId, setTelegramChatId] = useState("");
  const [discordEnabled, setDiscordEnabled] = useState(false);
  const [discordWebhookUrl, setDiscordWebhookUrl] = useState("");
  const [webhookEnabled, setWebhookEnabled] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("");

  const loadSettings = async () => {
    try {
      const data = await api.getNotificationSettings();
      setSettings(data);
      setEmailEnabled(data.email_enabled || false);
      setEmailAddress(data.email_address || "");
      setTelegramEnabled(data.telegram_enabled || false);
      setTelegramChatId(data.telegram_chat_id || "");
      setDiscordEnabled(data.discord_enabled || false);
      setDiscordWebhookUrl(data.discord_webhook_url || "");
      setWebhookEnabled(data.webhook_enabled || false);
      setWebhookUrl(data.webhook_url || "");
    } catch {
      toast.error("Failed to load notification settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const saveSettings = async () => {
    setSaving(true);
    try {
      await api.updateNotificationSettings({
        email_enabled: emailEnabled,
        email_address: emailAddress || null,
        telegram_enabled: telegramEnabled,
        telegram_chat_id: telegramChatId || null,
        discord_enabled: discordEnabled,
        discord_webhook_url: discordWebhookUrl || null,
        webhook_enabled: webhookEnabled,
        webhook_url: webhookUrl || null,
      });
      toast.success("Notification settings saved");
    } catch (err: any) {
      toast.error(err.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const testChannel = async (channel: string) => {
    setTesting(channel);
    try {
      const result = await api.testNotification(channel);
      if (result.success) {
        toast.success(`Test ${channel} notification sent!`);
      } else {
        toast.error(result.detail || `Failed to send test ${channel}`);
      }
    } catch (err: any) {
      toast.error(err.message || "Test failed");
    } finally {
      setTesting(null);
    }
  };

  const channels = [
    {
      id: "email",
      name: "Email",
      icon: EnvelopeIcon,
      color: "bg-blue-500/10 text-blue-400",
      enabled: emailEnabled,
      setEnabled: setEmailEnabled,
      fields: (
        <input
          type="email"
          value={emailAddress}
          onChange={(e) => setEmailAddress(e.target.value)}
          className="input mt-3"
          placeholder="you@example.com"
        />
      ),
    },
    {
      id: "telegram",
      name: "Telegram",
      icon: PaperAirplaneIcon,
      color: "bg-cyan-500/10 text-cyan-400",
      enabled: telegramEnabled,
      setEnabled: setTelegramEnabled,
      fields: (
        <div className="mt-3">
          <input
            type="text"
            value={telegramChatId}
            onChange={(e) => setTelegramChatId(e.target.value)}
            className="input"
            placeholder="Chat ID (e.g., 123456789)"
          />
          <p className="mt-1 text-xs text-slate-500">
            Message @BotFather to create a bot, then get your chat ID from @userinfobot
          </p>
        </div>
      ),
    },
    {
      id: "discord",
      name: "Discord",
      icon: BellIcon,
      color: "bg-indigo-500/10 text-indigo-400",
      enabled: discordEnabled,
      setEnabled: setDiscordEnabled,
      fields: (
        <div className="mt-3">
          <input
            type="url"
            value={discordWebhookUrl}
            onChange={(e) => setDiscordWebhookUrl(e.target.value)}
            className="input"
            placeholder="https://discord.com/api/webhooks/..."
          />
          <p className="mt-1 text-xs text-slate-500">
            Server Settings &gt; Integrations &gt; Webhooks &gt; New Webhook &gt; Copy URL
          </p>
        </div>
      ),
    },
    {
      id: "webhook",
      name: "Custom Webhook",
      icon: RssIcon,
      color: "bg-purple-500/10 text-purple-400",
      enabled: webhookEnabled,
      setEnabled: setWebhookEnabled,
      fields: (
        <div className="mt-3">
          <input
            type="url"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            className="input"
            placeholder="https://your-server.com/notifications"
          />
          <p className="mt-1 text-xs text-slate-500">
            Receives POST requests with JSON payload for each event
          </p>
        </div>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-800/50" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Notifications</h1>
        <p className="mt-1 text-sm text-slate-400">
          Configure how you receive alerts for security events, anomalies, and agent activity
        </p>
      </div>

      <div className="max-w-2xl space-y-4">
        {channels.map((ch) => (
          <motion.div
            key={ch.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`rounded-xl p-2.5 ${ch.color}`}>
                  <ch.icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{ch.name}</h3>
                  <p className="text-xs text-slate-400">
                    {ch.enabled ? "Enabled" : "Disabled"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {ch.enabled && (
                  <button
                    onClick={() => testChannel(ch.id)}
                    className="btn-secondary px-3 py-1.5 text-xs"
                    disabled={testing === ch.id}
                  >
                    {testing === ch.id ? "Sending..." : "Test"}
                  </button>
                )}
                <button
                  onClick={() => ch.setEnabled(!ch.enabled)}
                  className={`relative h-6 w-11 rounded-full transition-colors ${
                    ch.enabled ? "bg-brand-600" : "bg-slate-600"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                      ch.enabled ? "left-[22px]" : "left-0.5"
                    }`}
                  />
                </button>
              </div>
            </div>
            {ch.enabled && ch.fields}
          </motion.div>
        ))}

        <div className="pt-4">
          <button onClick={saveSettings} className="btn-primary w-full" disabled={saving}>
            {saving ? "Saving..." : "Save Notification Settings"}
          </button>
        </div>
      </div>
    </div>
  );
}
