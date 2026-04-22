import React from "react";
import { Link } from "react-router-dom";
import { StatusBadge, FailureBadge, TimeAgo, EmptyState, Spinner } from "./UI";

export default function PipelineTable({ pipelines, loading }) {
  if (loading) {
    return (
      <div className="flex justify-center py-10">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!pipelines.length) {
    return (
      <EmptyState message="No pipeline runs yet. Trigger a failure to start auto-healing." />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-border text-dim">
            <th className="text-left py-2 px-3 font-medium uppercase tracking-wider">Run</th>
            <th className="text-left py-2 px-3 font-medium uppercase tracking-wider">Repo</th>
            <th className="text-left py-2 px-3 font-medium uppercase tracking-wider hidden md:table-cell">Branch</th>
            <th className="text-left py-2 px-3 font-medium uppercase tracking-wider">Status</th>
            <th className="text-left py-2 px-3 font-medium uppercase tracking-wider hidden lg:table-cell">Failure</th>
            <th className="text-left py-2 px-3 font-medium uppercase tracking-wider hidden lg:table-cell">Actions</th>
            <th className="text-left py-2 px-3 font-medium uppercase tracking-wider">Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {pipelines.map((run) => (
            <tr
              key={run.run_id}
              className="hover:bg-muted/20 transition-colors group"
            >
              {/* Run ID */}
              <td className="py-2.5 px-3">
                <Link
                  to={`/pipelines/${run.run_id}`}
                  className="text-accent-cyan hover:underline font-mono text-xs"
                >
                  #{String(run.run_id).slice(-8)}
                </Link>
              </td>

              {/* Repo */}
              <td className="py-2.5 px-3">
                <span className="text-text truncate max-w-[120px] block">
                  {run.repo || "—"}
                </span>
              </td>

              {/* Branch */}
              <td className="py-2.5 px-3 hidden md:table-cell">
                <span className="text-dim">{run.branch || "—"}</span>
              </td>

              {/* Status */}
              <td className="py-2.5 px-3">
                <StatusBadge status={run.status} />
              </td>

              {/* Failure type */}
              <td className="py-2.5 px-3 hidden lg:table-cell">
                <FailureBadge type={run.failure_type} />
              </td>

              {/* Healing actions count */}
              <td className="py-2.5 px-3 hidden lg:table-cell">
                {run.healing_actions_count !== undefined
                  ? run.healing_actions_count > 0
                    ? (
                      <span className="text-accent-cyan">
                        {run.healing_actions_count} action{run.healing_actions_count !== 1 ? "s" : ""}
                      </span>
                    )
                    : <span className="text-dim">—</span>
                  : run.healing_actions?.length > 0
                    ? (
                      <span className="text-accent-cyan">
                        {run.healing_actions.length} action{run.healing_actions.length !== 1 ? "s" : ""}
                      </span>
                    )
                    : <span className="text-dim">—</span>
                }
              </td>

              {/* Time */}
              <td className="py-2.5 px-3">
                <TimeAgo dateStr={run.created_at} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
