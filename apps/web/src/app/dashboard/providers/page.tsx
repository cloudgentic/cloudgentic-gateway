"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import toast from "react-hot-toast";
import {
  Cog6ToothIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowTopRightOnSquareIcon,
  ChevronRightIcon,
  EyeIcon,
  EyeSlashIcon,
  ClipboardDocumentIcon,
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

interface ProviderDetail {
  setup_steps: string[];
  callback_url: string;
}

const CATEGORY_ORDER = [
  "Productivity",
  "Communication",
  "Social Media",
  "CRM",
  "Payments",
  "E-Commerce",
  "Developer Tools",
];

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

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [setupProvider, setSetupProvider] = useState<ProviderStatus | null>(null);
  const [setupStep, setSetupStep] = useState(0);
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [showSecret, setShowSecret] = useState(false);
  const [saving, setSaving] = useState(false);
  const [copiedCallback, setCopiedCallback] = useState(false);

  const callbackUrl = typeof window !== "undefined"
    ? `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8421"}/api/v1/accounts/{provider}/callback`
    : "";

  const loadProviders = async () => {
    try {
      const data = await api.listProviders();
      setProviders(data);
    } catch {
      toast.error("Failed to load providers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProviders();
  }, []);

  const openSetup = (provider: ProviderStatus) => {
    setSetupProvider(provider);
    setSetupStep(0);
    setClientId("");
    setClientSecret("");
    setShowSecret(false);
  };

  const saveCredentials = async () => {
    if (!setupProvider) return;
    setSaving(true);
    try {
      await api.configureProvider(setupProvider.provider, {
        provider: setupProvider.provider,
        client_id: clientId,
        client_secret: clientSecret,
      });
      toast.success(`${setupProvider.display_name} configured successfully!`);
      setSetupProvider(null);
      loadProviders();
    } catch (err: any) {
      toast.error(err.message || "Failed to save credentials");
    } finally {
      setSaving(false);
    }
  };

  const removeProvider = async (provider: string, name: string) => {
    if (!confirm(`Remove ${name} configuration? Users won't be able to connect new ${name} accounts.`)) return;
    try {
      await api.removeProviderConfig(provider);
      toast.success(`${name} configuration removed`);
      loadProviders();
    } catch (err: any) {
      toast.error(err.message || "Failed to remove configuration");
    }
  };

  const copyCallback = (provider: string) => {
    const url = callbackUrl.replace("{provider}", provider);
    navigator.clipboard.writeText(url);
    setCopiedCallback(true);
    setTimeout(() => setCopiedCallback(false), 2000);
  };

  const grouped = CATEGORY_ORDER.map((cat) => ({
    category: cat,
    items: providers.filter((p) => p.category === cat),
  })).filter((g) => g.items.length > 0);

  const configuredCount = providers.filter((p) => p.is_configured).length;

  // Setup steps for the wizard
  const SETUP_STEPS_DATA: Record<string, string[]> = {
    google: [
      "Go to Google Cloud Console and create or select a project",
      "Navigate to APIs & Services → Credentials",
      "Click 'Create Credentials' → 'OAuth client ID'",
      "If prompted, configure the OAuth consent screen (External type, fill in app name and your email)",
      "Application type: 'Web application'",
      "Name: 'CloudGentic Gateway'",
      "Under 'Authorized redirect URIs', add the callback URL shown below",
      "Click 'Create' and copy the Client ID and Client Secret",
    ],
    slack: [
      "Go to api.slack.com/apps and click 'Create New App'",
      "Choose 'From scratch', name it 'CloudGentic Gateway'",
      "Select your workspace",
      "Go to 'OAuth & Permissions' in the sidebar",
      "Under 'Redirect URLs', add the callback URL shown below",
      "Under 'Scopes' → 'User Token Scopes', add the scopes you need (channels:read, chat:write, etc.)",
      "Go to 'Basic Information' and copy the Client ID and Client Secret",
    ],
    twitter: [
      "Go to developer.x.com and sign in",
      "Navigate to the Developer Portal → Projects & Apps",
      "Create a new Project and App (or use existing)",
      "Go to App Settings → 'User authentication settings' → Set up",
      "App permissions: 'Read and write'",
      "Type of App: 'Web App'",
      "Add the callback URL shown below",
      "Copy the Client ID and Client Secret from 'Keys and tokens'",
    ],
    facebook: [
      "Go to developers.facebook.com → 'My Apps' → 'Create App'",
      "Choose app type: 'Business'",
      "Fill in app name: 'CloudGentic Gateway'",
      "Click 'Add Product' → 'Facebook Login' → 'Set Up' → Choose 'Web'",
      "Go to Facebook Login → Settings",
      "Add the callback URL to 'Valid OAuth Redirect URIs'",
      "Go to Settings → Basic for your App ID and App Secret",
    ],
    instagram: [
      "Instagram API uses Facebook's developer platform",
      "Go to developers.facebook.com → 'My Apps' → 'Create App' (Business type)",
      "Click 'Add Product' → 'Instagram' → 'Set Up'",
      "Go to Instagram → Basic Display → 'Create New App'",
      "Add the callback URL to 'Valid OAuth Redirect URIs'",
      "Copy the Instagram App ID and Instagram App Secret",
      "Note: You need a Facebook Page linked to an Instagram Business account",
    ],
    tiktok: [
      "Go to developers.tiktok.com and log in",
      "Click 'Manage Apps' → 'Create App'",
      "Fill in app details and description",
      "Under 'Platform', add 'Web' with your gateway URL",
      "Add the callback URL shown below as redirect URI",
      "Add the scopes/products you need (Video Kit, etc.)",
      "Submit for review (TikTok requires app review before use)",
      "Once approved, copy Client Key and Client Secret from app settings",
    ],
    stripe: [
      "Go to dashboard.stripe.com → Developers → API Keys",
      "For OAuth Connect: Go to Settings → Connect → Platform Settings",
      "Enable OAuth for your platform",
      "Add the callback URL shown below as redirect URI",
      "Copy the Client ID from Connect settings",
      "Copy the Secret Key from API Keys",
      "Tip: Use 'Test mode' keys during development",
    ],
    hubspot: [
      "Go to developers.hubspot.com and log in",
      "Click 'Apps' → 'Create App'",
      "Name: 'CloudGentic Gateway'",
      "Go to the 'Auth' tab",
      "Add the callback URL shown below as redirect URL",
      "Under 'Scopes', select the scopes your agents need",
      "Copy the Client ID and Client Secret from the 'Auth' tab",
    ],
    gohighlevel: [
      "Go to marketplace.gohighlevel.com and sign in as a developer",
      "Click 'My Apps' → 'Create App'",
      "Fill in app details",
      "Set the App Type to 'Sub-Account' or 'Agency' based on your needs",
      "Add the callback URL shown below as redirect URI",
      "Select the scopes/permissions your agents need",
      "Copy the Client ID and Client Secret from your app settings",
    ],
    salesforce: [
      "Log in to Salesforce → Setup (gear icon top right)",
      "Search for 'App Manager' in Quick Find",
      "Click 'New Connected App'",
      "Fill in App Name ('CloudGentic Gateway'), API Name, and Contact Email",
      "Check 'Enable OAuth Settings'",
      "Add the callback URL shown below",
      "Select OAuth Scopes (e.g., 'Full access' or specific scopes)",
      "Click 'Save' — may take 2-10 minutes to activate",
      "Go to 'Manage Consumer Details' for Consumer Key (Client ID) and Consumer Secret",
    ],
    discord: [
      "Go to discord.com/developers/applications",
      "Click 'New Application' and name it 'CloudGentic Gateway'",
      "Go to 'OAuth2' in the sidebar",
      "Add the callback URL shown below as a redirect",
      "Copy the Client ID and Client Secret",
    ],
    linkedin: [
      "Go to linkedin.com/developers/apps → 'Create App'",
      "Fill in app name, select or create a LinkedIn Page, upload a logo",
      "Go to the 'Auth' tab",
      "Add the callback URL shown below as redirect URL",
      "Under 'OAuth 2.0 scopes', request the scopes you need",
      "Copy the Client ID and Client Secret from the 'Auth' tab",
    ],
    github: [
      "Go to github.com → Settings → Developer settings → OAuth Apps",
      "Click 'New OAuth App'",
      "Application name: 'CloudGentic Gateway'",
      "Homepage URL: your gateway URL",
      "Authorization callback URL: the callback URL shown below",
      "Click 'Register application'",
      "Copy the Client ID, then click 'Generate a new client secret'",
    ],
    notion: [
      "Go to notion.so/my-integrations",
      "Click 'New integration'",
      "Name: 'CloudGentic Gateway', select your workspace",
      "Set type to 'Public' (for OAuth — default is Internal)",
      "Add the callback URL shown below as redirect URI",
      "Copy the OAuth Client ID and OAuth Client Secret",
      "Note: Users will need to grant specific page access when connecting",
    ],
    shopify: [
      "Go to partners.shopify.com and log in (create a free Partner account if needed)",
      "Click 'Apps' → 'Create app' → 'Create app manually'",
      "App name: 'CloudGentic Gateway'",
      "App URL: your gateway URL",
      "Add the callback URL shown below as 'Allowed redirection URL'",
      "Go to 'Client credentials' to find API Key (Client ID) and API Secret Key",
    ],
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Provider Setup</h1>
        <p className="mt-1 text-sm text-slate-400">
          Configure OAuth credentials for each provider you want to support.
          {configuredCount > 0 && (
            <span className="ml-2 text-emerald-400">
              {configuredCount} of {providers.length} configured
            </span>
          )}
        </p>
      </div>

      {/* Progress bar */}
      {providers.length > 0 && (
        <div className="mb-8">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="text-slate-400">Configuration Progress</span>
            <span className="text-slate-300">
              {configuredCount}/{providers.length} providers
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-700">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-brand-600 to-emerald-500"
              initial={{ width: 0 }}
              animate={{
                width: `${(configuredCount / Math.max(providers.length, 1)) * 100}%`,
              }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      )}

      {/* Provider list grouped by category */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-slate-800/50" />
          ))}
        </div>
      ) : (
        grouped.map((group) => (
          <div key={group.category} className="mb-8">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              {group.category}
            </h2>
            <div className="space-y-2">
              {group.items.map((provider) => (
                <motion.div
                  key={provider.provider}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="group flex items-center justify-between rounded-xl border border-slate-700/50 bg-slate-800/50 px-5 py-4 transition-all hover:border-slate-600 hover:bg-slate-800"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-xl border text-sm font-bold ${
                        PROVIDER_COLORS[provider.provider] || "bg-slate-700 text-slate-300 border-slate-600"
                      }`}
                    >
                      {PROVIDER_ICONS[provider.provider] || "?"}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-white">
                          {provider.display_name}
                        </h3>
                        {provider.is_configured ? (
                          <span className="badge-success flex items-center gap-1">
                            <CheckCircleIcon className="h-3 w-3" />
                            Configured
                          </span>
                        ) : (
                          <span className="badge-warning flex items-center gap-1">
                            <XCircleIcon className="h-3 w-3" />
                            Not configured
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-400">
                        {provider.description}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {provider.is_configured && (
                      <button
                        onClick={() => removeProvider(provider.provider, provider.display_name)}
                        className="rounded-lg px-3 py-1.5 text-xs text-red-400 transition-colors hover:bg-red-400/10"
                      >
                        Remove
                      </button>
                    )}
                    <button
                      onClick={() => openSetup(provider)}
                      className={`flex items-center gap-1 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                        provider.is_configured
                          ? "text-slate-300 hover:bg-slate-700"
                          : "bg-brand-600 text-white hover:bg-brand-700"
                      }`}
                    >
                      {provider.is_configured ? "Reconfigure" : "Set Up"}
                      <ChevronRightIcon className="h-4 w-4" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        ))
      )}

      {/* Setup Wizard Modal */}
      <Modal
        isOpen={!!setupProvider}
        onClose={() => setSetupProvider(null)}
        title={`Set Up ${setupProvider?.display_name || ""}`}
        size="lg"
      >
        {setupProvider && (
          <div>
            {/* Step indicator */}
            <div className="mb-6 flex items-center gap-2">
              <button
                onClick={() => setSetupStep(0)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
                  setupStep === 0
                    ? "bg-brand-600 text-white"
                    : "bg-slate-700 text-slate-400"
                }`}
              >
                1. Instructions
              </button>
              <div className="h-px flex-1 bg-slate-700" />
              <button
                onClick={() => setSetupStep(1)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
                  setupStep === 1
                    ? "bg-brand-600 text-white"
                    : "bg-slate-700 text-slate-400"
                }`}
              >
                2. Credentials
              </button>
            </div>

            <AnimatePresence mode="wait">
              {setupStep === 0 && (
                <motion.div
                  key="instructions"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  {/* Direct link */}
                  <a
                    href={setupProvider.setup_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mb-5 flex items-center justify-between rounded-xl border border-brand-500/30 bg-brand-500/5 p-4 transition-colors hover:bg-brand-500/10"
                  >
                    <div>
                      <p className="font-medium text-brand-300">
                        Open {setupProvider.display_name} Developer Console
                      </p>
                      <p className="text-xs text-brand-400/60">
                        {setupProvider.setup_url}
                      </p>
                    </div>
                    <ArrowTopRightOnSquareIcon className="h-5 w-5 text-brand-400" />
                  </a>

                  {/* Callback URL */}
                  <div className="mb-5 rounded-xl border border-slate-600 bg-slate-700/50 p-4">
                    <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-400">
                      Your Callback / Redirect URL
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 break-all rounded-lg bg-slate-800 px-3 py-2 text-sm text-emerald-400">
                        {callbackUrl.replace("{provider}", setupProvider.provider)}
                      </code>
                      <button
                        onClick={() => copyCallback(setupProvider.provider)}
                        className="rounded-lg bg-slate-600 p-2 text-slate-300 transition-colors hover:bg-slate-500"
                        title="Copy"
                      >
                        <ClipboardDocumentIcon className="h-4 w-4" />
                      </button>
                    </div>
                    {copiedCallback && (
                      <p className="mt-1 text-xs text-emerald-400">Copied!</p>
                    )}
                  </div>

                  {/* Steps */}
                  <div className="mb-6 space-y-3">
                    {(SETUP_STEPS_DATA[setupProvider.provider] || []).map(
                      (step, i) => (
                        <div key={i} className="flex gap-3">
                          <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-bold text-slate-300">
                            {i + 1}
                          </div>
                          <p className="text-sm leading-relaxed text-slate-300">
                            {step}
                          </p>
                        </div>
                      )
                    )}
                  </div>

                  {setupProvider.docs_url && (
                    <a
                      href={setupProvider.docs_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mb-6 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-300"
                    >
                      Official documentation
                      <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" />
                    </a>
                  )}

                  <button
                    onClick={() => setSetupStep(1)}
                    className="btn-primary w-full"
                  >
                    I have my credentials, continue
                  </button>
                </motion.div>
              )}

              {setupStep === 1 && (
                <motion.div
                  key="credentials"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <div className="space-y-5">
                    <div>
                      <label className="mb-1.5 block text-sm font-medium text-slate-300">
                        Client ID
                        <span className="ml-1 text-xs text-slate-500">
                          (also called App ID, Consumer Key, or API Key)
                        </span>
                      </label>
                      <input
                        type="text"
                        value={clientId}
                        onChange={(e) => setClientId(e.target.value)}
                        className="input font-mono text-sm"
                        placeholder="Paste your Client ID here"
                      />
                    </div>

                    <div>
                      <label className="mb-1.5 block text-sm font-medium text-slate-300">
                        Client Secret
                        <span className="ml-1 text-xs text-slate-500">
                          (also called App Secret, Consumer Secret, or API Secret)
                        </span>
                      </label>
                      <div className="relative">
                        <input
                          type={showSecret ? "text" : "password"}
                          value={clientSecret}
                          onChange={(e) => setClientSecret(e.target.value)}
                          className="input pr-10 font-mono text-sm"
                          placeholder="Paste your Client Secret here"
                        />
                        <button
                          type="button"
                          onClick={() => setShowSecret(!showSecret)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300"
                        >
                          {showSecret ? (
                            <EyeSlashIcon className="h-4 w-4" />
                          ) : (
                            <EyeIcon className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>

                    <div className="rounded-lg border border-slate-600/50 bg-slate-700/30 p-3">
                      <p className="text-xs text-slate-400">
                        Your credentials are encrypted with AES-256-GCM before
                        storage. They never leave your server.
                      </p>
                    </div>

                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={() => setSetupStep(0)}
                        className="btn-secondary flex-1"
                      >
                        Back
                      </button>
                      <button
                        onClick={saveCredentials}
                        className="btn-primary flex-1"
                        disabled={saving || !clientId || !clientSecret}
                      >
                        {saving ? "Saving..." : "Save & Enable"}
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </Modal>
    </div>
  );
}
