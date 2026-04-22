import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Pipelines from "./pages/Pipelines";
import PipelineDetail from "./pages/PipelineDetail";
import Analytics from "./pages/Analytics";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-void grid-bg">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/pipelines" element={<Pipelines />} />
            <Route path="/pipelines/:runId" element={<PipelineDetail />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>

        {/* Subtle footer */}
        <footer className="text-center py-4 text-xs font-mono text-dim/40 border-t border-border/30 mt-8">
          AutoHeal CI/CD Pipeline System · Self-Healing Infrastructure
        </footer>
      </div>
    </BrowserRouter>
  );
}
