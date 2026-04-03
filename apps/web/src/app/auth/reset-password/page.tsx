"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import toast from "react-hot-toast";
import {
  LockClosedIcon,
  CheckCircleIcon,
  ArrowLeftIcon,
} from "@heroicons/react/24/outline";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8421";

function ResetForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }

    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Reset failed");
      }

      setSuccess(true);
    } catch (err: any) {
      toast.error(err.message || "Failed to reset password");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="text-center">
        <h2 className="mb-2 text-xl font-bold text-white">Invalid Link</h2>
        <p className="mb-6 text-sm text-slate-400">
          This reset link is invalid or missing a token. Please request a new
          one.
        </p>
        <Link href="/auth/forgot-password" className="btn-primary">
          Request New Reset
        </Link>
      </div>
    );
  }

  if (success) {
    return (
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600/20">
          <CheckCircleIcon className="h-7 w-7 text-emerald-400" />
        </div>
        <h2 className="mb-2 text-xl font-bold text-white">
          Password Reset Successfully
        </h2>
        <p className="mb-6 text-sm text-slate-400">
          Your password has been updated. You can now log in with your new
          password.
        </p>
        <Link href="/auth/login" className="btn-primary inline-flex w-full">
          Go to Login
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600/20">
          <LockClosedIcon className="h-7 w-7 text-brand-400" />
        </div>
        <h2 className="text-xl font-bold text-white">Set New Password</h2>
        <p className="mt-2 text-sm text-slate-400">
          Enter your new password below
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-300">
            New Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
            placeholder="At least 8 characters"
            required
            minLength={8}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-300">
            Confirm Password
          </label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="input"
            placeholder="Repeat your new password"
            required
            minLength={8}
          />
        </div>

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={loading || !password || !confirmPassword}
        >
          {loading ? "Resetting..." : "Reset Password"}
        </button>
      </form>
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="rounded-2xl border border-slate-700 bg-slate-800 p-8 shadow-xl">
          <Suspense
            fallback={
              <div className="flex justify-center py-8">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
              </div>
            }
          >
            <ResetForm />
          </Suspense>

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
