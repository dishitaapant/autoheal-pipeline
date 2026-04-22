import React, { useState } from "react";
import { Link } from "react-router-dom";
import StatCards from "../components/StatCards";
import PipelineTable from "../components/PipelineTable";
import { TrendChart, FailureBreakdownChart, HealingActionsChart } from "../components/Charts";
import { SectionHeader } from "../components/UI";
import { useAnalytics, usePipelines } from "../hooks/useData";
import { webhookAPI } from "../utils/api";

export default function Dashboard() {
  const { analytics, loading: aLoading } = useAnalytics(8000);
  const { pipelines, loading: pLoading, refetch } = usePipelines(5000);
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState("");

  async function triggerDemo() {
    setTriggering(true);
    setTriggerMsg("");
    try {
      const res = await webhookAPI.triggerTestFailure();
      setTriggerMsg(`✓ Demo failure triggered (run: ${res.run_id})`);
      setTimeout(refetch, 2000);
    } catch (e) {
      setTriggerMsg(`✗ ${e.message}`);
    } finally {
      setTriggering(false);
    }
  }

  const recent = pipelines.slice(0, 8);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-xl font-bold text-bright">
            Pipeline Control Center
          </h1>
          <p className="text-xs font-mono text-dim mt-1">
            Real-time self-healing CI/CD monitoring
          </p>
        </div>
        <button
          onClick={triggerDemo}
          disabled={triggering}
          className="flex items-center gap-2 px-4 py-2 bg-accent-orange/10 border border-accent-orange/30
                     text-accent-orange text-xs font-mono rounded hover:bg-accent-orange/20 transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {triggering ? "⟳ Triggering…" : "⚡ Trigger Demo Failure"}
        </button>
      </div>

      {/* Trigger message */}
      {triggerMsg && (
        <div
          className={`px-4 py-2.5 rounded border text-xs font-mono animate-slide-up ${
            triggerMsg.startsWith("✓")
              ? "bg-accent-green/5 border-accent-green/20 text-accent-green"
              : "bg-accent-red/5 border-accent-red/20 text-accent-red"
          }`}
        >
          {triggerMsg}
        </div>
      )}

      {/* Stat cards */}
      <StatCards analytics={analytics} />

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TrendChart data={analytics?.daily_stats} />
        <FailureBreakdownChart data={analytics?.failure_type_breakdown} />
      </div>

      <HealingActionsChart data={analytics?.healing_action_breakdown} />

      {/* Recent pipelines */}
      <div className="panel p-5">
        <SectionHeader
          title="Recent Runs"
          subtitle={`${pipelines.length} total`}
          action={
            <Link
              to="/pipelines"
              className="text-xs font-mono text-accent-cyan hover:underline"
            >
              View all →
            </Link>
          }
        />
        <PipelineTable pipelines={recent} loading={pLoading} />
      </div>
    </div>
  );
}
