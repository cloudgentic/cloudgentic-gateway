import { ReactNode } from "react";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-700 bg-slate-800/50 py-16">
      <div className="mb-4 rounded-full bg-slate-700/50 p-4 text-slate-400">
        {icon}
      </div>
      <h3 className="mb-1 text-lg font-semibold text-white">{title}</h3>
      <p className="mb-6 max-w-sm text-center text-sm text-slate-400">
        {description}
      </p>
      {action}
    </div>
  );
}
