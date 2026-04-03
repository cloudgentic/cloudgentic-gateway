"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import toast from "react-hot-toast";
import {
  EnvelopeIcon,
  ClipboardDocumentIcon,
  CheckIcon,
  ArrowLeftIcon,
} from "@heroicons/react/24/outline";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8421";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    reset_token: string;
    reset_url: string;
    expires_in_minutes: number;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();

      if (data.reset_token) {
        setResult(data);
      } else {
        toast.success("If an account exists with that email, a reset has been initiated.");
      }
    } catch {
      toast.error("Failed to request password reset");
    } finally {
      setLoading(false);
    }
  };

  const copyResetLink = () => {
    if (!result) return;
    const fullUrl = `${window.location.origin}${result.reset_url}`;
    navigator.clipboard.writeText(fullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="rounded-2xl border border-slate-700 bg-slate-800 p-8 shadow-xl">
          {!result ? (
            <>
              <div className="mb-6 text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600/20">
                  <EnvelopeIcon className="h-7 w-7 text-brand-400" />
                </div>
                <h2 className="text-xl font-bold text-white">
                  Forgot Password
                </h2>
                <p className="mt-2 text-sm text-slate-400">
                  Enter your email address and we&apos;ll generate a password
                  reset link.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-300">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input"
                    placeholder="you@example.com"
                    required
                  />
                </div>

                <button
                  type="submit"
                  className="btn-primary w-full"
                  disabled={loading}
                >
                  {loading ? "Requesting..." : "Reset Password"}
                </button>
              </form>
            </>
          ) : (
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600/20">
                <CheckIcon className="h-7 w-7 text-emerald-400" />
              </div>
              <h2 className="mb-2 text-xl font-bold text-white">
                Reset Link Generated
              </h2>
              <p className="mb-6 text-sm text-slate-400">
                Use the link below to reset your password. It expires in{" "}
                <span className="text-yellow-400">
                  {result.expires_in_minutes} minutes
                </span>
                .
              </p>

              {/* Reset link */}
              <div className="mb-4 rounded-xl border border-slate-600 bg-slate-700/50 p-4">
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-400">
                  Reset Link
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 break-all rounded-lg bg-slate-800 px-3 py-2 text-left text-xs text-emerald-400">
                    {window.location.origin}{result.reset_url}
                  </code>
                  <button
                    onClick={copyResetLink}
                    className="rounded-lg bg-slate-600 p-2 text-slate-300 transition-colors hover:bg-slate-500"
                  >
                    {copied ? (
                      <CheckIcon className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <ClipboardDocumentIcon className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              <Link
                href={result.reset_url}
                className="btn-primary inline-flex w-full"
              >
                Reset Password Now
              </Link>

              <p className="mt-4 text-xs text-slate-500">
                In a production environment with SMTP configured, this link
                would be sent via email instead of being displayed here.
              </p>
            </div>
          )}

          <div className="mt-6 text-center">
            <Link
              href="/auth/login"
              className="inline-flex items-center gap-1.5 text-sm text-brand-400 hover:text-brand-300"
            >
              <ArrowLeftIcon className="h-3.5 w-3.5" />
              Back to login
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
