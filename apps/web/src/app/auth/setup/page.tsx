"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import { ShieldCheckIcon } from "@heroicons/react/24/outline";

export default function SetupPage() {
  const [step, setStep] = useState<"intro" | "qr" | "verify">("intro");
  const [qrData, setQrData] = useState<{
    secret: string;
    qr_code_base64: string;
  } | null>(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const { user, refreshUser } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user?.totp_enabled && user?.setup_complete) {
      router.replace("/dashboard");
    }
  }, [user, router]);

  const startSetup = async () => {
    setLoading(true);
    try {
      const data = await api.totpSetup();
      setQrData({ secret: data.secret, qr_code_base64: data.qr_code_base64 });
      setStep("qr");
    } catch (err: any) {
      toast.error(err.message || "Failed to start 2FA setup");
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await api.totpVerify(code);
      if (result.success) {
        toast.success("2FA enabled successfully!");
        await refreshUser();
        router.push("/dashboard");
      } else {
        toast.error(result.message);
      }
    } catch (err: any) {
      toast.error(err.message || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="rounded-2xl border border-slate-700 bg-slate-800 p-8 shadow-xl">
          {step === "intro" && (
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-600/20">
                <ShieldCheckIcon className="h-8 w-8 text-brand-400" />
              </div>
              <h2 className="mb-2 text-xl font-bold text-white">
                Set Up Two-Factor Authentication
              </h2>
              <p className="mb-6 text-sm text-slate-400">
                Two-factor authentication is required for all accounts. This
                adds an extra layer of security to protect your connected
                accounts and API keys.
              </p>
              <p className="mb-6 text-xs text-slate-500">
                You&apos;ll need an authenticator app like Google Authenticator,
                Authy, or 1Password.
              </p>
              <button
                onClick={startSetup}
                className="btn-primary w-full"
                disabled={loading}
              >
                {loading ? "Setting up..." : "Begin Setup"}
              </button>
            </div>
          )}

          {step === "qr" && qrData && (
            <div className="text-center">
              <h2 className="mb-2 text-xl font-bold text-white">
                Scan QR Code
              </h2>
              <p className="mb-6 text-sm text-slate-400">
                Scan this QR code with your authenticator app
              </p>

              <div className="mx-auto mb-6 inline-block rounded-xl bg-white p-4">
                <img
                  src={`data:image/png;base64,${qrData.qr_code_base64}`}
                  alt="TOTP QR Code"
                  className="h-48 w-48"
                />
              </div>

              <div className="mb-6">
                <p className="mb-1 text-xs text-slate-500">
                  Or enter this code manually:
                </p>
                <code className="rounded-lg bg-slate-700 px-3 py-1.5 text-sm font-mono text-brand-400">
                  {qrData.secret}
                </code>
              </div>

              <button
                onClick={() => setStep("verify")}
                className="btn-primary w-full"
              >
                I&apos;ve Scanned It
              </button>
            </div>
          )}

          {step === "verify" && (
            <form onSubmit={verifyCode} className="text-center">
              <h2 className="mb-2 text-xl font-bold text-white">
                Verify Your Code
              </h2>
              <p className="mb-6 text-sm text-slate-400">
                Enter the 6-digit code from your authenticator app
              </p>

              <input
                type="text"
                value={code}
                onChange={(e) =>
                  setCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                }
                className="input mb-6 text-center text-2xl tracking-[0.5em]"
                placeholder="000000"
                maxLength={6}
                autoFocus
              />

              <button
                type="submit"
                className="btn-primary w-full"
                disabled={loading || code.length !== 6}
              >
                {loading ? "Verifying..." : "Enable 2FA"}
              </button>

              <button
                type="button"
                onClick={() => setStep("qr")}
                className="mt-3 text-sm text-slate-400 hover:text-slate-300"
              >
                Back to QR code
              </button>
            </form>
          )}
        </div>
      </motion.div>
    </div>
  );
}
