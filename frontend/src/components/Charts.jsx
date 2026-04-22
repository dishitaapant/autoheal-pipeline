import React from "react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { SectionHeader } from "./UI";

const COLORS = {
  dependency_error: "#FFD700",
  build_error: "#FF4444",
  test_failure: "#FF6B35",
  timeout: "#8B5CF6",
  network_error: "#00D4FF",
  configuration_error: "#F59E0B",
  unknown: "#4A5568",
};

const TOOLTIP_STYLE = {
  backgroundColor: "#111820",
  border: "1px solid #1E2733",
  borderRadius: "6px",
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: "11px",
  color: "#C9D1D9",
};

export function TrendChart({ data }) {
  if (!data || !data.length) return null;
  return (
    <div className="panel p-5 animate-fade-in">
      <SectionHeader
        title="Pipeline Activity"
        subtitle="7-day failure & heal trend"
      />
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="gradTotal" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradHealed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00FF87" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#00FF87" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1E2733" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: "#4A5568", fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "#4A5568", fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Area
            type="monotone"
            dataKey="total"
            stroke="#00D4FF"
            strokeWidth={1.5}
            fill="url(#gradTotal)"
            name="Total"
          />
          <Area
            type="monotone"
            dataKey="healed"
            stroke="#00FF87"
            strokeWidth={1.5}
            fill="url(#gradHealed)"
            name="Healed"
          />
          <Area
            type="monotone"
            dataKey="failed"
            stroke="#FF4444"
            strokeWidth={1.5}
            fill="none"
            strokeDasharray="4 2"
            name="Failed"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function FailureBreakdownChart({ data }) {
  const chartData = Object.entries(data || {})
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name: key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
      value,
      key,
    }));

  if (!chartData.length) return null;

  return (
    <div className="panel p-5 animate-fade-in">
      <SectionHeader
        title="Failure Types"
        subtitle="Distribution of detected failures"
      />
      <div className="flex items-center gap-4">
        <ResponsiveContainer width="50%" height={160}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map(({ key }) => (
                <Cell key={key} fill={COLORS[key] || "#4A5568"} />
              ))}
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex flex-col gap-2 flex-1 min-w-0">
          {chartData.map(({ name, value, key }) => (
            <div key={key} className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: COLORS[key] || "#4A5568" }}
              />
              <span className="text-xs font-mono text-dim truncate">{name}</span>
              <span className="ml-auto text-xs font-mono text-bright font-semibold">
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function HealingActionsChart({ data }) {
  const chartData = Object.entries(data || {})
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name: key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()).substring(0, 16),
      value,
    }))
    .sort((a, b) => b.value - a.value);

  if (!chartData.length) return null;

  return (
    <div className="panel p-5 animate-fade-in">
      <SectionHeader
        title="Healing Actions"
        subtitle="Actions executed during auto-healing"
      />
      <ResponsiveContainer width="100%" height={180}>
        <BarChart
          data={chartData}
          margin={{ top: 4, right: 4, bottom: 20, left: -20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1E2733" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 9, fill: "#4A5568", fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
            angle={-20}
            textAnchor="end"
          />
          <YAxis
            tick={{ fontSize: 10, fill: "#4A5568", fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Bar dataKey="value" fill="#00D4FF" radius={[3, 3, 0, 0]} opacity={0.8} name="Count" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
