import React from "react";

const ACTION_META = {
  install_dependencies: { icon: "⬇", label: "Install Dependencies", color: "text-accent-yellow" },
  retry_pipeline: { icon: "⟳", label: "Retry Pipeline", color: "text-accent-cyan" },
  clear_cache: { icon: "◌", label: "Clear Cache", color: "text-accent-purple" },
  rerun_failed_job: { icon: "▶", label: "Re-run Failed Job", color: "text-accent-cyan" },
  update_dependencies: { icon: "↑", label: "Update Dependencies", color: "text-accent-yellow" },
  fix_configuration: { icon: "⚙", label: "Fix Configuration", color: "text-accent-orange" },
  no_action: { icon: "—", label: "No Action", color: "text-dim" },
};

function formatTime(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function HealingTimeline({ actions, status, healed }) {
  if (!actions || actions.length === 0) {
    return (
      <div className="panel p-5">
        <p className="text-xs font-mono text-dim">No healing actions have been executed.</p>
      </div>
    );
  }

  return (
    <div className="panel p-5">
      <div className="flex items-center gap-3 mb-5">
        <span className="text-xs font-mono text-dim uppercase tracking-widest">
          Healing Timeline
        </span>
        {healed ? (
          <span className="badge-success ml-auto">✓ HEALED</span>
        ) : status === "failed_healing" ? (
          <span className="badge-failure ml-auto">✗ HEAL FAILED</span>
        ) : null}
      </div>

      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-3.5 top-0 bottom-0 w-px bg-border" />

        <div className="space-y-4">
          {actions.map((action, i) => {
            const meta = ACTION_META[action.action_type] || ACTION_META.no_action;
            return (
              <div key={i} className="flex gap-4 relative animate-slide-up" style={{ animationDelay: `${i * 60}ms` }}>
                {/* Icon dot */}
                <div
                  className={`w-7 h-7 rounded-full border flex items-center justify-center shrink-0 z-10 bg-panel
                    ${action.success ? "border-accent-green/40 bg-accent-green/5" : "border-accent-red/40 bg-accent-red/5"}`}
                >
                  <span className={`text-xs ${meta.color}`}>{meta.icon}</span>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 pb-1">
                  <div className="flex items-start justify-between gap-2 flex-wrap">
                    <span className={`text-xs font-mono font-semibold ${meta.color}`}>
                      {meta.label}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-xs font-mono ${action.success ? "text-accent-green" : "text-accent-red"}`}>
                        {action.success ? "✓ OK" : "✗ FAIL"}
                      </span>
                      <span className="text-xs font-mono text-dim">
                        {formatTime(action.executed_at)}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-dim mt-0.5">{action.description}</p>
                  {action.output && (
                    <div className="mt-2 bg-void border border-border rounded px-2.5 py-1.5">
                      <p className="text-xs font-mono text-text/70 break-all">{action.output}</p>
                    </div>
                  )}
                  {action.retry_count > 0 && (
                    <span className="text-xs font-mono text-dim mt-1 block">
                      Retried {action.retry_count}×
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
