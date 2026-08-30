import { useState, useEffect } from 'react';
import { Activity, Database, Server, Cpu, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  python_version: string;
  database_status: string;
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/health');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data: HealthResponse = await res.json();
      setHealth(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to connect to backend service';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-semibold text-lg tracking-tight text-white">CAREFlow India</h1>
            <p className="text-xs text-slate-400">Healthcare Operational Intelligence & Capacity Platform</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Phase 1 Foundation
          </span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700 disabled:opacity-50"
            title="Refresh Health Check"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 flex flex-col gap-6">
        <section className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
            System Operational Status
          </h2>

          {loading && !health && (
            <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
              <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
              <span>Verifying backend service status...</span>
            </div>
          )}

          {error && (
            <div className="bg-rose-950/40 border border-rose-800/60 rounded-lg p-4 flex items-start gap-3 text-rose-300">
              <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-sm">Backend Service Unreachable</p>
                <p className="text-xs text-rose-400/80 mt-1">{error}</p>
                <p className="text-xs text-slate-400 mt-2">
                  Ensure FastAPI backend is running via <code className="bg-slate-950 px-1 py-0.5 rounded text-amber-400">uvicorn backend.app.main:app</code> on port 8000.
                </p>
              </div>
            </div>
          )}

          {health && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium">API Service</span>
                  <Server className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="text-lg font-semibold text-white capitalize">{health.status}</span>
                </div>
                <span className="text-xs text-slate-500 mt-2">{health.app_name} v{health.version}</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium">Database Connection</span>
                  <Database className="w-4 h-4 text-blue-400" />
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="text-lg font-semibold text-white capitalize">{health.database_status}</span>
                </div>
                <span className="text-xs text-slate-500 mt-2">SQLAlchemy + SQLite / PG adapter</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium">Python Engine</span>
                  <Cpu className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-lg font-semibold text-white">v{health.python_version}</div>
                <span className="text-xs text-slate-500 mt-2">Verified ML compatible runtime</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium">Environment</span>
                  <Activity className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="text-lg font-semibold text-white capitalize">{health.environment}</div>
                <span className="text-xs text-slate-500 mt-2 truncate">{new Date(health.timestamp).toLocaleTimeString()}</span>
              </div>
            </div>
          )}
        </section>

        {/* Phase 1 Architecture Summary */}
        <section className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Phase 1 Foundation Infrastructure
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="font-semibold text-emerald-400 block mb-1">Backend Architecture</span>
              FastAPI + Pydantic v2 + SQLAlchemy 2.0. Modular router with health probes and async database handlers.
            </div>
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="font-semibold text-blue-400 block mb-1">Frontend Stack</span>
              React 18 + TypeScript + Vite + Tailwind CSS v4. Configured for proxying API calls to port 8000.
            </div>
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="font-semibold text-amber-400 block mb-1">Data Layer Isolation</span>
              Immutable <code className="text-slate-200">data/raw/</code>, <code className="text-slate-200">data/interim/</code>, and <code className="text-slate-200">data/processed/</code> pipeline layers ready for HMIS ingestion.
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/30 px-6 py-3 text-xs text-slate-500 flex justify-between items-center">
        <span>CAREFlow India &copy; 2026 — HMIS Operational Healthcare Intelligence Platform</span>
        <span>Phase 1 Verified Foundation</span>
      </footer>
    </div>
  );
}
