"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import toast from "react-hot-toast";
import Link from "next/link";
import {
  DocumentDuplicateIcon,
  CheckCircleIcon,
  ArrowLeftIcon,
  ShieldCheckIcon,
  ClockIcon,
  NoSymbolIcon,
  EyeIcon,
} from "@heroicons/react/24/outline";

const CATEGORY_ICONS: Record<string, string> = {
  email: "bg-blue-500/10 text-blue-400",
  safety: "bg-green-500/10 text-green-400",
  social: "bg-pink-500/10 text-pink-400",
  general: "bg-purple-500/10 text-purple-400",
};

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState<string | null>(null);
  const [applied, setApplied] = useState<Set<string>>(new Set());

  const loadTemplates = async () => {
    try {
      const data = await api.listRuleTemplates();
      setTemplates(data.templates || []);
    } catch {
      toast.error("Failed to load templates");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const applyTemplate = async (id: string, name: string) => {
    if (!confirm(`Apply template "${name}"? This will create rules for your account.`)) return;
    setApplying(id);
    try {
      const rules = await api.applyRuleTemplate(id);
      toast.success(`Template applied! ${Array.isArray(rules) ? rules.length : 0} rules created.`);
      setApplied((prev) => new Set([...prev, id]));
    } catch (err: any) {
      toast.error(err.message || "Failed to apply template");
    } finally {
      setApplying(null);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <Link
          href="/dashboard/rules"
          className="mb-4 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-300"
        >
          <ArrowLeftIcon className="h-3.5 w-3.5" />
          Back to Rules
        </Link>
        <h1 className="text-2xl font-bold text-white">Rule Templates</h1>
        <p className="mt-1 text-sm text-slate-400">
          Pre-built rule configurations for common use cases. Apply with one click.
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl bg-slate-800/50" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((t, i) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="card flex flex-col justify-between"
            >
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`rounded-lg p-2 ${
                        CATEGORY_ICONS[t.category] || CATEGORY_ICONS.general
                      }`}
                    >
                      <DocumentDuplicateIcon className="h-4 w-4" />
                    </div>
                    <h3 className="font-semibold text-white">{t.name}</h3>
                  </div>
                  {applied.has(t.id) && (
                    <CheckCircleIcon className="h-5 w-5 text-green-400" />
                  )}
                </div>
                <p className="mb-3 text-sm text-slate-400">{t.description}</p>
                {t.tags && (
                  <div className="mb-4 flex flex-wrap gap-1">
                    {t.tags.map((tag: string) => (
                      <span
                        key={tag}
                        className="rounded-full bg-slate-700/50 px-2 py-0.5 text-xs text-slate-400"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <p className="text-xs text-slate-500">
                  {t.rules?.length || 0} rules &middot; v{t.version || "1.0.0"}
                </p>
              </div>
              <button
                onClick={() => applyTemplate(t.id, t.name)}
                className={`mt-4 w-full ${
                  applied.has(t.id) ? "btn-secondary" : "btn-primary"
                }`}
                disabled={applying === t.id}
              >
                {applying === t.id
                  ? "Applying..."
                  : applied.has(t.id)
                  ? "Applied"
                  : "Apply Template"}
              </button>
            </motion.div>
          ))}
        </div>
      )}

      {!loading && templates.length === 0 && (
        <div className="py-16 text-center">
          <p className="text-slate-500">No templates available.</p>
        </div>
      )}
    </div>
  );
}
