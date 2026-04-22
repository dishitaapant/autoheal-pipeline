import React, { useState } from "react";

const ERROR_PATTERNS = [
  { re: /(error|ERROR|Error)/g, cls: "text-accent-red" },
  { re: /(FAILED|failed|FAIL)/g, cls: "text-accent-red" },
  { re: /(WARNING|warning|WARN|warn)/g, cls: "text-accent-yellow" },
  { re: /(ModuleNotFoundError|ImportError|SyntaxError|TypeError|AssertionError)/g, cls: "text-accent-orange font-bold" },
  { re: /(PASSED|passed|SUCCESS|success)/g, cls: "text-accent-green" },
  { re: /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/g, cls: "text-dim" },
];

function HighlightedLine({ line }) {
  if (!line.trim()) return <span className="block h-3" />;

  let lower = line.toLowerCase();
  let baseColor = "text-text";

  if (lower.includes("error") || lower.includes("failed") || lower.includes("fatal")) {
    baseColor = "text-accent-red/90";
  } else if (lower.includes("warn")) {
    baseColor = "text-accent-yellow/90";
  } else if (lower.includes("pass") || lower.includes("success") || lower.includes("ok")) {
    baseColor = "text-accent-green/80";
  } else if (line.startsWith("#") || line.startsWith("=")) {
    baseColor = "text-accent-cyan/70";
  } else if (lower.includes("info") || lower.includes("step")) {
    baseColor = "text-dim";
  }

  return (
    <span className={`block leading-5 ${baseColor}`}>
      {line}
    </span>
  );
}

export default function LogViewer({ logs, title = "Raw Logs" }) {
  const [filter, setFilter] = useState("");
  const [showErrors, setShowErrors] = useState(false);

  if (!logs) {
    return (
      <div className="panel p-5">
        <p className="text-xs font-mono text-dim">No logs available for this run.</p>
      </div>
    );
  }

  const lines = logs.split("\n");
  const filtered = lines.filter((line) => {
    if (showErrors) {
      return /error|fail|warn|except/i.test(line);
    }
    if (filter) {
      return line.toLowerCase().includes(filter.toLowerCase());
    }
    return true;
  });

  return (
    <div className="panel p-5">
      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-3 flex-wrap">
        <span className="text-xs font-mono text-dim uppercase tracking-widest">{title}</span>
        <div className="flex-1 min-w-0">
          <input
            type="text"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full max-w-xs bg-void border border-border rounded px-2 py-1 text-xs font-mono text-text
                       focus:outline-none focus:border-accent-cyan/50 placeholder:text-dim"
          />
        </div>
        <button
          onClick={() => setShowErrors((v) => !v)}
          className={`text-xs font-mono px-3 py-1 rounded border transition-colors ${
            showErrors
              ? "bg-accent-red/10 border-accent-red/30 text-accent-red"
              : "border-border text-dim hover:text-text"
          }`}
        >
          Errors only
        </button>
        <span className="text-xs font-mono text-dim ml-auto">
          {filtered.length}/{lines.length} lines
        </span>
      </div>

      {/* Log area */}
      <div className="log-viewer bg-void rounded-lg border border-border p-4 max-h-80 overflow-auto">
        {filtered.length === 0 ? (
          <span className="text-dim text-xs">No lines match the current filter.</span>
        ) : (
          filtered.map((line, i) => (
            <HighlightedLine key={i} line={line} />
          ))
        )}
      </div>
    </div>
  );
}
