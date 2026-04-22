import React from "react";

export function StatusBadge({ status }) {
  const map = {
    success: { cls: "badge-success", icon: "✓", label: "SUCCESS" },
    healed: { cls: "badge-success", icon: "⟳", label: "HEALED" },
    failure: { cls: "badge-failure", icon: "✗", label: "FAILURE" },
    failed_healing: { cls: "badge-failure", icon: "✗", label: "HEAL FAILED" },
    healing: { cls: "badge-healing", icon: "◎", label: "HEALING" },
    running: { cls: "badge-healing", icon: "▶", label: "RUNNING" },
    pending: { cls: "badge-neutral", icon: "○", label: "PENDING" },
  };
  const { cls, icon, label } = map[status] || map.pending;
  return (
    <span className={cls}>
      <span>{icon}</span>
      {label}
    </span>
  );
}

export function FailureBadge({ type }) {
  const map = {
    dependency_error: { cls: "badge-warning", label: "DEP ERROR" },
    build_error: { cls: "badge-failure", label: "BUILD ERROR" },
    test_failure: { cls: "badge-warning", label: "TEST FAIL" },
    timeout: { cls: "badge-neutral", label: "TIMEOUT" },
    network_error: { cls: "badge-neutral", label: "NETWORK" },
    configuration_error: { cls: "badge-warning", label: "CONFIG" },
    unknown: { cls: "badge-neutral", label: "UNKNOWN" },
  };
  if (!type) return null;
  const { cls, label } = map[type] || map.unknown;
  return <span className={cls}>{label}</span>;
}

export function Spinner({ size = "sm" }) {
  const s = size === "lg" ? "h-8 w-8 border-2" : "h-4 w-4 border";
  return (
    <div
      className={`${s} border-accent-cyan border-t-transparent rounded-full animate-spin`}
    />
  );
}

export function EmptyState({ message = "No data available" }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-dim">
      <div className="text-4xl mb-3 opacity-30">◈</div>
      <p className="font-mono text-sm">{message}</p>
    </div>
  );
}

export function TimeAgo({ dateStr }) {
  if (!dateStr) return <span className="text-dim">—</span>;
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);

  let label;
  if (diff < 60) label = `${diff}s ago`;
  else if (diff < 3600) label = `${Math.floor(diff / 60)}m ago`;
  else if (diff < 86400) label = `${Math.floor(diff / 3600)}h ago`;
  else label = `${Math.floor(diff / 86400)}d ago`;

  return (
    <span className="font-mono text-xs text-dim" title={date.toLocaleString()}>
      {label}
    </span>
  );
}

export function SectionHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h2 className="font-display text-sm font-semibold text-bright tracking-widest uppercase">
          {title}
        </h2>
        {subtitle && <p className="text-xs text-dim mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
