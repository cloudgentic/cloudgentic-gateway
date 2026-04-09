"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [isFirstRun, setIsFirstRun] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [needsTotp, setNeedsTotp] = useState(false);
  const [loading, setLoading] = useState(false);
  const { user, login, register, refreshUser } = useAuth();
  const router = useRouter();

  useEffect(() => {
    api.setupStatus().then((status) => {
      if (!status.has_admin) {
        setIsRegister(true);
        setIsFirstRun(true);
      }
    });
  }, []);

  useEffect(() => {
    // Only redirect if user is loaded AND we didn't just arrive from a failed session
    if (user && !loading) {
      // Verify the token is actually valid before redirecting
      api.getMe().then((me) => {
        if (!me.totp_enabled) {
          router.replace("/auth/setup");
        } else {
          router.replace("/dashboard");
        }
      }).catch(() => {
        // Token is stale — clear it and stay on login
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      });
    }
  }, [user, loading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8421";

    try {
      if (isRegister) {
        await register(email, password, displayName || undefined);
        router.push("/auth/setup");
      } else {
        // Direct fetch to bypass API client 401 interception
        const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            password,
            totp_code: totpCode || null,
          }),
        });

        const data = await res.json();

        if (!res.ok) {
          const detail = data.detail || "Login failed";
          if (detail === "TOTP code required") {
            setNeedsTotp(true);
            setLoading(false);
            return;
          }
          throw new Error(detail);
        }

        // Success — store tokens and load user
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        await refreshUser();

        if (data.requires_2fa_setup) {
          router.push("/auth/setup");
        } else {
          router.push("/dashboard");
        }
      }
    } catch (err: any) {
      toast.error(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 shadow-lg shadow-brand-600/25">
            <span className="text-xl font-bold text-white">CG</span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            {isFirstRun ? "Welcome to CloudGentic Gateway" : "CloudGentic Gateway"}
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            {isFirstRun
              ? "Create your admin account to get started"
              : isRegister
              ? "Create an account"
              : "Sign in to your account"}
          </p>
        </div>

        {/* Form */}
        <div className="rounded-2xl border border-slate-700 bg-slate-800 p-8 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            {isRegister && (
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-300">
                  Display Name
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="input"
                  placeholder="Your name"
                />
              </div>
            )}

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                Email
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

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="Enter your password"
                required
                minLength={8}
              />
            </div>

            {needsTotp && !isRegister && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
              >
                <label className="mb-1.5 block text-sm font-medium text-slate-300">
                  Two-Factor Code
                </label>
                <input
                  type="text"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  className="input text-center tracking-[0.5em]"
                  placeholder="000000"
                  maxLength={6}
                  autoFocus
                />
              </motion.div>
            )}

            {!isRegister && (
              <div className="text-right">
                <a
                  href="/auth/forgot-password"
                  className="text-xs text-slate-400 transition-colors hover:text-brand-400"
                >
                  Forgot password?
                </a>
              </div>
            )}

            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : isRegister ? (
                "Create Account"
              ) : needsTotp ? (
                "Verify & Sign In"
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {!isFirstRun && (
            <div className="mt-6 text-center">
              <button
                onClick={() => {
                  setIsRegister(!isRegister);
                  setNeedsTotp(false);
                }}
                className="text-sm text-brand-400 transition-colors hover:text-brand-300"
              >
                {isRegister
                  ? "Already have an account? Sign in"
                  : "Need an account? Register"}
              </button>
            </div>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-slate-600">
          CloudGentic Gateway v0.1.0
        </p>
      </motion.div>
    </div>
  );
}
