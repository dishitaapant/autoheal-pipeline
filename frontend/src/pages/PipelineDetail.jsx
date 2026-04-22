import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { StatusBadge, FailureBadge, TimeAgo, Spinner } from "../components/UI";
import HealingTimeline from "../components/HealingTimeline";
import LogViewer from "../components/LogViewer";
import { pipelineAPI } from "../utils/api";

export default function PipelineDetail() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let interval;
    async function fetch() {
      try {
        const data = await pipelineAPI.get(runId);
        setRun(data);
        setError(null);
        // Stop polling if terminal state
        if (["healed", "failed_healing", "success", "failure"].includes(data.status)) {
          clearInterval(interval);
        }
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    fetch();
    interval = setInterval(fetch, 3000);
    return () => clearInterval(interval);
  }, [runId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-48">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="panel p-8 text-center">
        <p className="text-accent-red font-mono text-sm mb-4">
          {error || "Pipeline run not found"}
        </p>
        <Link to="/pipelines" className="text-xs font-mono text-accent-cyan hover:underline">
          ← Back to pipelines
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs font-mono text-dim">
        <Link to="/" className="hover:text-text">Dashboard</Link>
        <span>/</span>
        <Link to="/pipelines" className="hover:text-text">Pipelines</Link>
        <span>/</span>
        <span className="text-text">#{String(run.run_id).slice(-12)}</span>
      </div>

      {/* Header */}
      <div className="panel p-5">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <StatusBadge status={run.status} />
              <FailureBadge type={run.failure_type} />
              {run.healed && (
                <span className="text-xs font-mono text-accent-green">
                  ✓ Auto-healed
                </span>
              )}
            </div>
            <h1 className="font-display text-lg font-bold text-bright">
              {run.workflow_name || "CI Pipeline"}
            </h1>
            <div className="flex items-center gap-4 mt-2 flex-wrap text-xs font-mono text-dim">
              <span>{run.repo}</span>
              <span>⎇ {run.branch}</span>
              {run.job_name && <span>job: {run.job_name}</span>}
              {run.actor && <span>by {run.actor}</span>}
            </div>
          </div>
          <div className="text-right text-xs font-mono text-dim shrink-0">
            <div>Run ID</div>
            <div className="text-text">{run.run_id}</div>
            <div className="mt-1">
              <TimeAgo dateStr={run.created_at} />
            </div>
          </div>
        </div>

        {/* Failure message */}
        {run.failure_message && (
          <div className="mt-4 bg-void border border-accent-red/20 rounded p-3">
            <p className="text-xs font-mono text-accent-red/80 leading-relaxed">
              ⚠ {run.failure_message}
            </p>
          </div>
        )}

        {/* Commit */}
        {run.commit_sha && (
          <div className="mt-3 text-xs font-mono text-dim">
            commit{" "}
            <span className="text-accent-cyan">{run.commit_sha.slice(0, 12)}</span>
          </div>
        )}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Healing timeline */}
        <div>
          <h2 className="text-xs font-mono text-dim uppercase tracking-widest mb-3">
            Healing Actions
          </h2>
          <HealingTimeline
            actions={run.healing_actions}
            status={run.status}
            healed={run.healed}
          />
        </div>

        {/* Details panel */}
        <div>
          <h2 className="text-xs font-mono text-dim uppercase tracking-widest mb-3">
            Run Details
          </h2>
          <div className="panel p-5 space-y-3">
            {[
              ["Run ID", run.run_id],
              ["Repository", run.repo],
              ["Branch", run.branch],
              ["Workflow", run.workflow_name],
              ["Job", run.job_name || "—"],
              ["Actor", run.actor || "—"],
              ["Commit", run.commit_sha?.slice(0, 16) || "—"],
              ["Status", run.status],
              ["Failure Type", run.failure_type || "—"],
              ["Healed", run.healed ? "Yes" : "No"],
              ["Retry Count", run.retry_count ?? 0],
              ["Actions Taken", run.healing_actions?.length ?? 0],
            ].map(([label, value]) => (
              <div key={label} className="flex items-start justify-between gap-4">
                <span className="text-xs font-mono text-dim shrink-0">{label}</span>
                <span className="text-xs font-mono text-text text-right break-all">
                  {String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Logs */}
      <div>
        <h2 className="text-xs font-mono text-dim uppercase tracking-widest mb-3">
          Pipeline Logs
        </h2>
        <LogViewer logs={run.raw_logs} title="Raw Logs" />
      </div>
    </div>
  );
}
