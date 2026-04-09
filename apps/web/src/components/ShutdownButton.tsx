"use client";

import { useState } from "react";
import { PowerIcon } from "@heroicons/react/24/outline";
import { motion, AnimatePresence } from "framer-motion";

export function ShutdownButton() {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isShuttingDown, setIsShuttingDown] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deploymentMode = process.env.NEXT_PUBLIC_DEPLOYMENT_MODE || "self-hosted";
  if (deploymentMode === "cloud") return null;

  const handleShutdown = async () => {
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8421";
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${apiUrl}/api/v1/system/shutdown`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.detail || `Shutdown failed (${res.status})`);
        return;
      }

      setIsShuttingDown(true);
    } catch {
      // Network error after request sent — server is already shutting down
      setIsShuttingDown(true);
    }
  };

  return (
    <>
      <button
        onClick={() => setShowConfirm(true)}
        className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-500 transition-colors hover:bg-slate-800 hover:text-red-400"
      >
        <PowerIcon className="h-4 w-4" />
        Shutdown Gateway
      </button>
      <AnimatePresence>
        {showConfirm && (
          <ShutdownModal
            isShuttingDown={isShuttingDown}
            error={error}
            onConfirm={handleShutdown}
            onCancel={() => { setShowConfirm(false); setError(null); }}
          />
        )}
      </AnimatePresence>
    </>
  );
}

function ShutdownModal({
  isShuttingDown,
  error,
  onConfirm,
  onCancel,
}: {
  isShuttingDown: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onCancel}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="mx-4 w-full max-w-sm rounded-2xl border border-slate-700 bg-slate-800 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {isShuttingDown ? (
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-red-400 border-t-transparent" />
            </div>
            <h3 className="text-lg font-semibold text-white">Shutting Down...</h3>
            <p className="mt-2 text-sm text-slate-400">
              All Gateway services are stopping. You can close this window.
            </p>
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/10">
                <PowerIcon className="h-5 w-5 text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-white">Shutdown Gateway?</h3>
            </div>
            <p className="mb-6 text-sm text-slate-400">
              This will stop all Gateway services (API, dashboard, database, Redis, workers).
              You will need to run{" "}
              <code className="rounded bg-slate-700 px-1.5 py-0.5 text-xs text-slate-300">
                docker compose up -d
              </code>{" "}
              to restart.
            </p>
            {error && (
              <p className="mb-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {error}
              </p>
            )}
            <div className="flex gap-3">
              <button
                onClick={onCancel}
                className="flex-1 rounded-lg border border-slate-600 px-4 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={onConfirm}
                className="flex-1 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-500"
              >
                Shutdown
              </button>
            </div>
          </>
        )}
      </motion.div>
    </motion.div>
  );
}
