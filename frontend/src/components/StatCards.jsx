import React from "react";

const ICONS = {
  total: "▦",
  healed: "⟳",
  failed: "✗",
  rate: "◈",
};

export default function StatCards({ analytics }) {
  if (!analytics) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="stat-card animate-pulse h-28">
            <div className="h-3 w-20 bg-muted rounded mb-3" />
            <div className="h-8 w-16 bg-muted rounded" />
          </div>
        ))}
      </div>
    );
  }

  const {
    total_runs,
    total_failures,
    successful_heals,
    failed_heals,
    heal_success_rate,
    total_successes,
  } = analytics;

  const cards = [
    {
      label: "Total Runs",
      value: total_runs,
      sub: `${total_successes} passed`,
      icon: ICONS.total,
      color: "text-accent-cyan",
      glow: "before:bg-accent-cyan",
    },
    {
      label: "Failures Detected",
      value: total_failures,
      sub: "pipeline failures",
      icon: ICONS.failed,
      color: "text-accent-red",
      glow: "before:bg-accent-red",
    },
    {
      label: "Healed",
      value: successful_heals,
      sub: `${failed_heals} unresolved`,
      icon: ICONS.healed,
      color: "text-accent-green",
      glow: "before:bg-accent-green",
    },
    {
      label: "Heal Rate",
      value: `${heal_success_rate}%`,
      sub: "auto-resolution",
      icon: ICONS.rate,
      color: heal_success_rate >= 70 ? "text-accent-green" : heal_success_rate >= 40 ? "text-accent-yellow" : "text-accent-red",
      glow: heal_success_rate >= 70 ? "before:bg-accent-green" : "before:bg-accent-yellow",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ label, value, sub, icon, color, glow }) => (
        <div
          key={label}
          className={`stat-card animate-fade-in
            before:absolute before:top-0 before:left-0 before:w-0.5 before:h-full ${glow} before:opacity-60`}
        >
          <div className="flex items-start justify-between mb-3">
            <span className="text-xs font-mono text-dim uppercase tracking-widest">
              {label}
            </span>
            <span className={`text-lg ${color} opacity-60`}>{icon}</span>
          </div>
          <div className={`font-display text-3xl font-bold ${color} mb-1`}>
            {value}
          </div>
          <div className="text-xs font-mono text-dim">{sub}</div>
        </div>
      ))}
    </div>
  );
}
