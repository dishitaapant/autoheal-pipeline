import React from "react";
import { TrendChart, FailureBreakdownChart, HealingActionsChart } from "../components/Charts";
import StatCards from "../components/StatCards";
import { Spinner } from "../components/UI";
import { useAnalytics } from "../hooks/useData";

export default function Analytics() {
  const { analytics, loading, error } = useAnalytics(10000);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-48">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel p-6 text-center">
        <p className="text-accent-red font-mono text-sm">Failed to load analytics: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="font-display text-xl font-bold text-bright">Analytics</h1>
        <p className="text-xs font-mono text-dim mt-1">
          Healing performance and failure intelligence
        </p>
      </div>

      <StatCards analytics={analytics} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <TrendChart data={analytics?.daily_stats} />
        <FailureBreakdownChart data={analytics?.failure_type_breakdown} />
      </div>

      <HealingActionsChart data={analytics?.healing_action_breakdown} />

      {/* Heal rate gauge */}
      {analytics && (
        <div className="panel p-6">
          <h2 className="text-xs font-mono text-dim uppercase tracking-widest mb-4">
            Auto-Heal Effectiveness
          </h2>
          <div className="flex items-end gap-6">
            <div>
              <div
                className={`font-display text-6xl font-bold ${
                  analytics.heal_success_rate >= 70
                    ? "text-accent-green"
                    : analytics.heal_success_rate >= 40
                    ? "text-accent-yellow"
                    : "text-accent-red"
                }`}
              >
                {analytics.heal_success_rate}%
              </div>
              <div className="text-xs font-mono text-dim mt-1">
                of failures auto-resolved
              </div>
            </div>
            <div className="flex-1 space-y-2 pb-1">
              <div className="flex justify-between text-xs font-mono text-dim">
                <span>Heal rate</span>
                <span>{analytics.heal_success_rate}%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${analytics.heal_success_rate}%`,
                    background:
                      analytics.heal_success_rate >= 70
                        ? "#00FF87"
                        : analytics.heal_success_rate >= 40
                        ? "#FFD700"
                        : "#FF4444",
                  }}
                />
              </div>
              <div className="flex gap-6 text-xs font-mono">
                <span className="text-accent-green">
                  ✓ {analytics.successful_heals} healed
                </span>
                <span className="text-accent-red">
                  ✗ {analytics.failed_heals} unresolved
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
