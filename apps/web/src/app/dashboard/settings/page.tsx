"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import {
  UserCircleIcon,
  KeyIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  EyeSlashIcon,
} from "@heroicons/react/24/outline";
import { formatDate } from "@/lib/utils";

export default function SettingsPage() {
  const { user, refreshUser, logout } = useAuth();

  // Profile
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [savingProfile, setSavingProfile] = useState(false);

  // Password
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);

  // 2FA Reset
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetPassword, setResetPassword] = useState("");
  const [resetting2fa, setResetting2fa] = useState(false);
  const [qrData, setQrData] = useState<{
    secret: string;
    qr_code_base64: string;
  } | null>(null);
  const [verifyCode, setVerifyCode] = useState("");
  const [verifying, setVerifying] = useState(false);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await api.updateMe({ display_name: displayName });
      await refreshUser();
      toast.success("Profile updated");
    } catch (err: any) {
      toast.error(err.message || "Failed to update profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast.error("New passwords don't match");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setSavingPassword(true);
    try {
      await api.changePassword(currentPassword, newPassword);
      toast.success("Password changed successfully");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      toast.error(err.message || "Failed to change password");
    } finally {
      setSavingPassword(false);
    }
  };

  const handleReset2FA = async () => {
    if (!resetPassword) {
      toast.error("Enter your current password to confirm");
      return;
    }

    setResetting2fa(true);
    try {
      // Verify password first by attempting login
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8421";
      const loginRes = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: user?.email,
          password: resetPassword,
          totp_code: null,
        }),
      });

      // If TOTP required, password is correct — proceed to get new TOTP
      const loginData = await loginRes.json();
      if (
        loginRes.ok ||
        loginData.detail === "TOTP code required"
      ) {
        // Password verified — generate new TOTP
        const data = await api.totpSetup();
        setQrData({
          secret: data.secret,
          qr_code_base64: data.qr_code_base64,
        });
        setShowResetConfirm(false);
        setResetPassword("");
      } else {
        toast.error("Incorrect password");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to reset 2FA");
    } finally {
      setResetting2fa(false);
    }
  };

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    setVerifying(true);
    try {
      const result = await api.totpVerify(verifyCode);
      if (result.success) {
        toast.success("2FA updated successfully");
        setQrData(null);
        setVerifyCode("");
        await refreshUser();
      } else {
        toast.error(result.message);
      }
    } catch (err: any) {
      toast.error(err.message || "Verification failed");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-slate-400">
          Manage your account, security, and preferences
        </p>
      </div>

      <div className="max-w-2xl space-y-6">
        {/* Account Info */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-brand-600/10 p-2.5">
              <UserCircleIcon className="h-5 w-5 text-brand-400" />
            </div>
            <div>
              <h2 className="font-semibold text-white">Profile</h2>
              <p className="text-xs text-slate-400">
                Your account information
              </p>
            </div>
          </div>

          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                Email
              </label>
              <input
                type="email"
                value={user?.email || ""}
                className="input opacity-60"
                disabled
              />
              <p className="mt-1 text-xs text-slate-500">
                Email cannot be changed
              </p>
            </div>

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

            <div className="flex items-center justify-between border-t border-slate-700 pt-4">
              <div className="text-xs text-slate-500">
                <p>
                  Account created:{" "}
                  {user?.created_at ? formatDate(user.created_at) : "-"}
                </p>
                <p>
                  Role: {user?.is_admin ? "Admin" : "User"}
                </p>
              </div>
              <button
                type="submit"
                className="btn-primary"
                disabled={savingProfile}
              >
                {savingProfile ? "Saving..." : "Save Profile"}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Change Password */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-yellow-500/10 p-2.5">
              <KeyIcon className="h-5 w-5 text-yellow-400" />
            </div>
            <div>
              <h2 className="font-semibold text-white">Change Password</h2>
              <p className="text-xs text-slate-400">
                Update your account password
              </p>
            </div>
          </div>

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                Current Password
              </label>
              <div className="relative">
                <input
                  type={showCurrentPw ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="input pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPw(!showCurrentPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300"
                >
                  {showCurrentPw ? (
                    <EyeSlashIcon className="h-4 w-4" />
                  ) : (
                    <EyeIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                New Password
              </label>
              <div className="relative">
                <input
                  type={showNewPw ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="At least 8 characters"
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPw(!showNewPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300"
                >
                  {showNewPw ? (
                    <EyeSlashIcon className="h-4 w-4" />
                  ) : (
                    <EyeIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                Confirm New Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input"
                placeholder="Repeat new password"
                required
                minLength={8}
              />
            </div>

            <div className="flex justify-end border-t border-slate-700 pt-4">
              <button
                type="submit"
                className="btn-primary"
                disabled={
                  savingPassword ||
                  !currentPassword ||
                  !newPassword ||
                  !confirmPassword
                }
              >
                {savingPassword ? "Changing..." : "Change Password"}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Two-Factor Authentication */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-emerald-500/10 p-2.5">
              <ShieldCheckIcon className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="font-semibold text-white">
                Two-Factor Authentication
              </h2>
              <p className="text-xs text-slate-400">
                Manage your authenticator app
              </p>
            </div>
          </div>

          <div className="mb-4 flex items-center gap-2">
            <CheckCircleIcon className="h-5 w-5 text-emerald-400" />
            <span className="text-sm text-emerald-400">
              2FA is enabled on your account
            </span>
          </div>

          {!qrData && !showResetConfirm && (
            <div>
              <p className="mb-4 text-sm text-slate-400">
                If you lost access to your authenticator app or want to switch
                to a different device, you can reset your 2FA and set up a new
                one.
              </p>
              <button
                onClick={() => setShowResetConfirm(true)}
                className="btn-secondary"
              >
                <ExclamationTriangleIcon className="mr-2 h-4 w-4 text-yellow-400" />
                Reset 2FA
              </button>
            </div>
          )}

          {showResetConfirm && !qrData && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-4"
            >
              <div className="mb-3 flex items-center gap-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
                <h3 className="font-medium text-yellow-300">
                  Confirm 2FA Reset
                </h3>
              </div>
              <p className="mb-4 text-sm text-yellow-200/70">
                Enter your current password to confirm. Your existing
                authenticator codes will stop working.
              </p>
              <div className="mb-4">
                <input
                  type="password"
                  value={resetPassword}
                  onChange={(e) => setResetPassword(e.target.value)}
                  className="input"
                  placeholder="Current password"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setShowResetConfirm(false);
                    setResetPassword("");
                  }}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReset2FA}
                  className="btn-danger flex-1"
                  disabled={resetting2fa || !resetPassword}
                >
                  {resetting2fa ? "Resetting..." : "Reset 2FA"}
                </button>
              </div>
            </motion.div>
          )}

          {qrData && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <p className="text-sm text-slate-300">
                Scan this QR code with your authenticator app:
              </p>

              <div className="flex justify-center">
                <div className="rounded-xl bg-white p-4">
                  <img
                    src={`data:image/png;base64,${qrData.qr_code_base64}`}
                    alt="TOTP QR Code"
                    className="h-48 w-48"
                  />
                </div>
              </div>

              <div className="text-center">
                <p className="mb-1 text-xs text-slate-500">
                  Manual entry code:
                </p>
                <code className="rounded-lg bg-slate-700 px-3 py-1.5 font-mono text-sm text-brand-400">
                  {qrData.secret}
                </code>
              </div>

              <form onSubmit={handleVerify2FA} className="space-y-3">
                <input
                  type="text"
                  value={verifyCode}
                  onChange={(e) =>
                    setVerifyCode(
                      e.target.value.replace(/\D/g, "").slice(0, 6)
                    )
                  }
                  className="input text-center text-2xl tracking-[0.5em]"
                  placeholder="000000"
                  maxLength={6}
                  autoFocus
                />
                <button
                  type="submit"
                  className="btn-primary w-full"
                  disabled={verifying || verifyCode.length !== 6}
                >
                  {verifying ? "Verifying..." : "Verify & Enable"}
                </button>
              </form>
            </motion.div>
          )}
        </motion.div>

        {/* Danger Zone */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-xl border border-red-500/20 bg-red-500/5 p-6"
        >
          <h2 className="mb-1 font-semibold text-red-400">Danger Zone</h2>
          <p className="mb-4 text-sm text-red-300/60">
            Irreversible actions — proceed with caution
          </p>
          <button
            onClick={() => {
              if (
                confirm(
                  "Are you sure you want to log out of all sessions?"
                )
              ) {
                logout();
              }
            }}
            className="btn-danger"
          >
            Log Out All Sessions
          </button>
        </motion.div>
      </div>
    </div>
  );
}
