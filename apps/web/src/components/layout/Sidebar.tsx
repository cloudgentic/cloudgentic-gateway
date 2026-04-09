"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import { ShutdownButton } from "@/components/ShutdownButton";
import {
  HomeIcon,
  LinkIcon,
  KeyIcon,
  ShieldCheckIcon,
  ShieldExclamationIcon,
  ClipboardDocumentListIcon,
  ArrowLeftOnRectangleIcon,
  Cog6ToothIcon,
  WrenchScrewdriverIcon,
  BoltIcon,
  BellIcon,
  HeartIcon,
  UsersIcon,
  RssIcon,
} from "@heroicons/react/24/outline";

const navigation = [
  { name: "Overview", href: "/dashboard", icon: HomeIcon },
  { name: "Provider Setup", href: "/dashboard/providers", icon: Cog6ToothIcon },
  { name: "Connected Accounts", href: "/dashboard/accounts", icon: LinkIcon },
  { name: "API Keys", href: "/dashboard/keys", icon: KeyIcon },
  { name: "Agents", href: "/dashboard/agents", icon: UsersIcon },
  { name: "Rules", href: "/dashboard/rules", icon: ShieldCheckIcon },
  { name: "Webhooks", href: "/dashboard/webhooks", icon: RssIcon },
  { name: "Security", href: "/dashboard/security", icon: ShieldExclamationIcon },
  { name: "Health", href: "/dashboard/health", icon: HeartIcon },
  { name: "Audit Log", href: "/dashboard/audit", icon: ClipboardDocumentListIcon },
  { name: "Notifications", href: "/dashboard/notifications", icon: BellIcon },
  { name: "Settings", href: "/dashboard/settings", icon: WrenchScrewdriverIcon },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-700 bg-slate-900">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-slate-700 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
          <span className="text-sm font-bold text-white">CG</span>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-white">CloudGentic</h1>
          <p className="text-xs text-slate-400">Gateway</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-brand-600/10 text-brand-400"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5 flex-shrink-0",
                  isActive ? "text-brand-400" : "text-slate-500 group-hover:text-slate-400"
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="border-t border-slate-700 p-4">
        <Link
          href="/dashboard/settings"
          className="group mb-3 flex items-center gap-3 rounded-lg px-2 py-2 transition-all hover:bg-slate-800"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600/20 text-brand-400">
            <span className="text-sm font-medium">
              {user?.email?.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-slate-200">
              {user?.display_name || user?.email}
            </p>
            <p className="truncate text-xs text-slate-500">{user?.email}</p>
          </div>
          <WrenchScrewdriverIcon className="h-4 w-4 text-slate-600 transition-colors group-hover:text-slate-400" />
        </Link>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-500 transition-colors hover:bg-slate-800 hover:text-red-400"
        >
          <ArrowLeftOnRectangleIcon className="h-4 w-4" />
          Log out
        </button>
        <ShutdownButton />
      </div>
    </aside>
  );
}
