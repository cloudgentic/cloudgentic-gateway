"use client";

import { EmptyState } from "@/components/ui/EmptyState";
import { ShieldCheckIcon } from "@heroicons/react/24/outline";

export default function ApprovalsPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Pending Approvals</h1>
        <p className="mt-1 text-sm text-slate-400">
          Review and approve actions that require manual confirmation
        </p>
      </div>

      <EmptyState
        icon={<ShieldCheckIcon className="h-8 w-8" />}
        title="No pending approvals"
        description="When rules require manual approval, pending requests will appear here"
      />
    </div>
  );
}
