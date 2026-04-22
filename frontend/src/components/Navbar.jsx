import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useHealth } from "../hooks/useData";

export default function Navbar() {
  const location = useLocation();
  const health = useHealth();
  const isHealthy = health?.status === "healthy";

  const links = [
    { to: "/", label: "Dashboard" },
    { to: "/pipelines", label: "Pipelines" },
    { to: "/analytics", label: "Analytics" },
  ];

  return (
    <header className="h-14 border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-50 flex items-center px-6 gap-8">
      {/* Logo */}
      <div className="flex items-center gap-2.5 shrink-0">
        <div className="w-7 h-7 rounded bg-accent-cyan/10 border border-accent-cyan/30 flex items-center justify-center">
          <span className="text-accent-cyan text-xs font-mono font-bold">⟳</span>
        </div>
        <span className="font-display font-semibold text-bright text-sm tracking-wide">
          AutoHeal
        </span>
        <span className="text-dim text-xs font-mono hidden sm:block">/CI</span>
      </div>

      {/* Nav links */}
      <nav className="flex gap-1">
        {links.map(({ to, label }) => {
          const active = location.pathname === to;
          return (
            <Link
              key={to}
              to={to}
              className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                active
                  ? "bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20"
                  : "text-dim hover:text-text hover:bg-muted/50"
              }`}
            >
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* System status */}
      <div className="flex items-center gap-2 text-xs font-mono">
        <span
          className={`status-dot ${isHealthy ? "active" : health ? "failure" : "healing"}`}
        />
        <span className="text-dim hidden sm:block">
          {health ? (isHealthy ? "SYSTEM NOMINAL" : "DEGRADED") : "CONNECTING…"}
        </span>
      </div>
    </header>
  );
}
