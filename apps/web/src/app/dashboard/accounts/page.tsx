"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, ConnectedAccount } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { EmptyState } from "@/components/ui/EmptyState";
import toast from "react-hot-toast";
import Link from "next/link";
import {
  LinkIcon,
  TrashIcon,
  ArrowTopRightOnSquareIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

interface ProviderStatus {
  provider: string;
  display_name: string;
  is_configured: boolean;
  category: string;
  description: string;
  setup_url: string;
  docs_url: string | null;
}

const PROVIDER_COLORS: Record<string, string> = {
  google: "bg-red-500/10 text-red-400 border-red-500/20",
  slack: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  twitter: "bg-slate-500/10 text-slate-300 border-slate-500/20",
  facebook: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  instagram: "bg-pink-500/10 text-pink-400 border-pink-500/20",
  tiktok: "bg-slate-500/10 text-slate-300 border-slate-500/20",
  stripe: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  hubspot: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  gohighlevel: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  salesforce: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  discord: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  linkedin: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  github: "bg-slate-500/10 text-slate-300 border-slate-500/20",
  notion: "bg-slate-500/10 text-slate-300 border-slate-500/20",
  shopify: "bg-green-500/10 text-green-400 border-green-500/20",
};

const PROVIDER_ICONS: Record<string, string> = {
  google: "G",
  slack: "S",
  twitter: "X",
  facebook: "f",
  instagram: "IG",
  tiktok: "TT",
  stripe: "$",
  hubspot: "H",
  gohighlevel: "GL",
  salesforce: "SF",
  discord: "D",
  linkedin: "in",
  github: "GH",
  notion: "N",
  shopify: "S",
};

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [accountsData, providersData] = await Promise.all([
        api.listAccounts().catch(() => []),
        api.listProviders().catch(() => []),
      ]);
      setAccounts(accountsData);
      setProviders(providersData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const connectAccount = async (provider: string) => {
    try {
      const data = await api.startOAuth(provider);
      window.location.href = data.authorization_url;
    } catch (err: any) {
      toast.error(err.message || "Failed to start connection");
    }
  };

  const disconnectAccount = async (accountId: string) => {
    if (!confirm("Are you sure you want to disconnect this account?")) return;
    try {
      await api.disconnectAccount(accountId);
      toast.success("Account disconnected");
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to disconnect");
    }
  };

  const configuredProviders = providers.filter((p) => p.is_configured);
  const unconfiguredProviders = providers.filter((p) => !p.is_configured);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Connected Accounts</h1>
        <p className="mt-1 text-sm text-slate-400">
          Connect your external accounts to let AI agents act on your behalf
        </p>
      </div>

      {/* Alert if no providers configured */}
      {!loading && configuredProviders.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-5"
        >
          <div className="flex items-start gap-3">
            <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-400" />
            <div>
              <h3 className="font-medium text-yellow-300">
                No providers configured yet
              </h3>
              <p className="mt-1 text-sm text-yellow-200/70">
                Before you can connect accounts, you need to set up OAuth
                credentials for at least one provider.
              </p>
              <Link
                href="/dashboard/providers"
                className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-yellow-500/20 px-4 py-2 text-sm font-medium text-yellow-300 transition-colors hover:bg-yellow-500/30"
              >
                <Cog6ToothIcon className="h-4 w-4" />
                Go to Provider Setup
              </Link>
            </div>
          </div>
        </motion.div>
      )}

      {/* Configured Providers — available to connect */}
      {configuredProviders.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
            Available Providers
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {configuredProviders.map((provider) => {
              const connected = accounts.find(
                (a) => a.provider === provider.provider
              );
              const color =
                PROVIDER_COLORS[provider.provider] ||
                "bg-slate-700 text-slate-300 border-slate-600";
              const icon = PROVIDER_ICONS[provider.provider] || "?";

              return (
                <motion.div
                  key={provider.provider}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="card group"
                >
                  <div className="mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-xl border text-lg font-bold ${color}`}
                      >
                        {icon}
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">
                          {provider.display_name}
                        </h3>
                        <p className="text-xs text-slate-400">
                          {provider.description}
                        </p>
                      </div>
                    </div>
                    {connected && (
                      <span className="badge-success">Connected</span>
                    )}
                  </div>

                  {connected ? (
                    <div className="flex items-center justify-between border-t border-slate-700 pt-4">
                      <div>
                        <p className="text-sm text-slate-300">
                          {connected.provider_email || connected.display_name}
                        </p>
                        <p className="text-xs text-slate-500">
                          Connected {formatDate(connected.created_at)}
                        </p>
                      </div>
                      <button
                        onClick={() => disconnectAccount(connected.id)}
                        className="rounded-lg p-2 text-red-400 transition-colors hover:bg-red-400/10"
                        title="Disconnect"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => connectAccount(provider.provider)}
                      className="btn-primary w-full"
                    >
                      <ArrowTopRightOnSquareIcon className="mr-2 h-4 w-4" />
                      Connect {provider.display_name}
                    </button>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Not yet configured providers */}
      {unconfiguredProviders.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
            Not Yet Configured
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {unconfiguredProviders.map((provider) => {
              const color =
                PROVIDER_COLORS[provider.provider] ||
                "bg-slate-700 text-slate-300 border-slate-600";
              const icon = PROVIDER_ICONS[provider.provider] || "?";

              return (
                <div
                  key={provider.provider}
                  className="flex items-center gap-3 rounded-xl border border-dashed border-slate-700 bg-slate-800/30 px-4 py-3 opacity-60"
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-lg border text-sm font-bold ${color}`}
                  >
                    {icon}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-400">
                      {provider.display_name}
                    </p>
                    <p className="text-xs text-slate-600">
                      {provider.description}
                    </p>
                  </div>
                  <Link
                    href="/dashboard/providers"
                    className="text-xs text-brand-400 hover:text-brand-300"
                  >
                    Set up
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Connected Accounts List */}
      {accounts.length > 0 && (
        <div>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
            Your Connected Accounts
          </h2>
          <div className="space-y-3">
            {accounts.map((account) => {
              const color =
                PROVIDER_COLORS[account.provider] ||
                "bg-slate-700 text-slate-400 border-slate-600";
              const icon = PROVIDER_ICONS[account.provider] || "?";

              return (
                <motion.div
                  key={account.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="card flex items-center justify-between"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-xl border text-lg font-bold ${color}`}
                    >
                      {icon}
                    </div>
                    <div>
                      <p className="font-medium text-white">
                        {account.display_name || account.provider_email}
                      </p>
                      <p className="text-sm text-slate-400">
                        {account.provider} &middot;{" "}
                        {account.scopes?.length || 0} scopes
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="badge-success">Active</span>
                    <button
                      onClick={() => disconnectAccount(account.id)}
                      className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-400/10 hover:text-red-400"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {!loading && accounts.length === 0 && configuredProviders.length > 0 && (
        <EmptyState
          icon={<LinkIcon className="h-8 w-8" />}
          title="No accounts connected"
          description="Click 'Connect' on any provider above to link your account"
        />
      )}
    </div>
  );
}
