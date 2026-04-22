import React, { useState } from "react";
import PipelineTable from "../components/PipelineTable";
import { SectionHeader } from "../components/UI";
import { usePipelines } from "../hooks/useData";

const STATUS_FILTERS = ["all", "failure", "healing", "healed", "failed_healing", "success"];

export default function Pipelines() {
  const { pipelines, loading, refetch } = usePipelines(5000);
  const [statusFilter, setStatusFilter] = useState("all");
  const [search, setSearch] = useState("");

  const filtered = pipelines.filter((p) => {
    const matchStatus = statusFilter === "all" || p.status === statusFilter;
    const matchSearch =
      !search ||
      p.repo?.toLowerCase().includes(search.toLowerCase()) ||
      p.run_id?.toLowerCase().includes(search.toLowerCase()) ||
      p.branch?.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-xl font-bold text-bright">Pipeline Runs</h1>
          <p className="text-xs font-mono text-dim mt-1">
            {pipelines.length} total runs · auto-refreshing every 5s
          </p>
        </div>
        <button
          onClick={refetch}
          className="text-xs font-mono px-3 py-1.5 border border-border text-dim
                     hover:text-text hover:border-accent-cyan/30 rounded transition-colors"
        >
          ⟳ Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="panel p-4 flex items-center gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Search repo, branch, run ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-void border border-border rounded px-3 py-1.5 text-xs font-mono text-text
                     focus:outline-none focus:border-accent-cyan/50 placeholder:text-dim w-56"
        />
        <div className="flex gap-1 flex-wrap">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`text-xs font-mono px-2.5 py-1 rounded border transition-colors ${
                statusFilter === s
                  ? "bg-accent-cyan/10 border-accent-cyan/30 text-accent-cyan"
                  : "border-border text-dim hover:text-text"
              }`}
            >
              {s.replace("_", " ").toUpperCase()}
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs font-mono text-dim">
          {filtered.length} results
        </span>
      </div>

      <div className="panel p-5">
        <PipelineTable pipelines={filtered} loading={loading} />
      </div>
    </div>
  );
}
