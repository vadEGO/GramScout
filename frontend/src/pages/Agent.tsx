import { useEffect, useState } from "react";

const API = "/api/v1";

interface AgentStatus {
  accounts: { total: number; active: number; warming: number; banned: number };
  channels: { total: number; targets: number };
  tasks: { pending: number };
  workflows: { running: number };
  can_comment: boolean;
  can_react: boolean;
  needs_warming: boolean;
}

interface Workflow {
  id: string;
  name: string;
  status: string;
  current_step: number;
  total_steps: number;
  stats: Record<string, any>;
  created_at: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  steps: number;
}

const WORKFLOW_TEMPLATES = [
  { id: "full_pipeline", name: "Full Growth Pipeline", icon: "🚀", desc: "Import → Proxy → Warm → Parse → Comment → React", color: "from-blue-500 to-violet-500" },
  { id: "quick_boost", name: "Quick Channel Boost", icon: "⚡", desc: "Use warm accounts to boost a specific channel", color: "from-amber-500 to-orange-500" },
  { id: "account_recovery", name: "Account Recovery", icon: "🔄", desc: "Recover and re-warm banned accounts", color: "from-emerald-500 to-teal-500" },
  { id: "revenue_generation", name: "Revenue Generation", icon: "💰", desc: "Post affiliate links, track conversions", color: "from-pink-500 to-rose-500" },
];

export default function AgentDashboard() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    Promise.all([
      fetch(`${API}/agent/status`).then((r) => r.json()),
      fetch(`${API}/agent/workflows`).then((r) => r.json()),
    ])
      .then(([s, w]) => { setStatus(s); setWorkflows(w); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const createAndStartWorkflow = async (templateId: string) => {
    const res = await fetch(`${API}/agent/workflows/create?template_id=${templateId}`, { method: "POST" });
    const data = await res.json();
    if (data.id) {
      await fetch(`${API}/agent/workflows/${data.id}/start`, { method: "POST" });
    }
    load();
  };

  const bulkWarm = async () => {
    await fetch(`${API}/agent/bulk/warm-all`, { method: "POST" });
    load();
  };

  const bulkAssignProxies = async () => {
    await fetch(`${API}/agent/bulk/assign-proxies`, { method: "POST" });
    load();
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin-slow"></div></div>;
  }

  const readinessScore = status ? Math.round(
    ((status.accounts.active / Math.max(status.accounts.total, 1)) * 40) +
    (status.channels.targets > 0 ? 30 : 0) +
    (status.accounts.active > 5 ? 30 : (status.accounts.active / 5) * 30)
  ) : 0;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Agent Control</h1>
          <p className="text-gray-500 text-sm mt-1">Autonomous operation dashboard for OpenClaw</p>
        </div>
        <div className="flex gap-2">
          <button onClick={bulkWarm} className="btn-ghost text-sm">🔥 Warm All</button>
          <button onClick={bulkAssignProxies} className="btn-ghost text-sm">🌐 Assign Proxies</button>
          <button onClick={load} className="btn-ghost text-sm">↻ Refresh</button>
        </div>
      </div>

      {/* Readiness Score */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">System Readiness</h3>
          <span className={`text-2xl font-bold ${readinessScore >= 80 ? "text-emerald-400" : readinessScore >= 50 ? "text-amber-400" : "text-red-400"}`}>
            {readinessScore}%
          </span>
        </div>
        <div className="progress-bar" style={{ height: "10px" }}>
          <div className="progress-bar-fill" style={{
            width: `${readinessScore}%`,
            background: readinessScore >= 80 ? "#10b981" : readinessScore >= 50 ? "#f59e0b" : "#ef4444",
          }} />
        </div>
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div className="flex items-center gap-2">
            <span className={status?.accounts.active ? "text-emerald-400" : "text-red-400"}>{status?.accounts.active ? "✓" : "✗"}</span>
            <span className="text-sm text-gray-400">Active Accounts</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={status?.channels.targets ? "text-emerald-400" : "text-red-400"}>{status?.channels.targets ? "✓" : "✗"}</span>
            <span className="text-sm text-gray-400">Target Channels</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={status?.can_comment ? "text-emerald-400" : "text-amber-400"}>{status?.can_comment ? "✓" : "○"}</span>
            <span className="text-sm text-gray-400">Can Comment</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={!status?.needs_warming ? "text-emerald-400" : "text-amber-400"}>{!status?.needs_warming ? "✓" : "○"}</span>
            <span className="text-sm text-gray-400">Warm Accounts</span>
          </div>
        </div>
      </div>

      {/* Fleet Stats */}
      <div className="grid grid-cols-6 gap-3">
        {[
          { label: "Total", value: status?.accounts.total || 0, color: "text-blue-400" },
          { label: "Active", value: status?.accounts.active || 0, color: "text-emerald-400" },
          { label: "Warming", value: status?.accounts.warming || 0, color: "text-amber-400" },
          { label: "Banned", value: status?.accounts.banned || 0, color: "text-red-400" },
          { label: "Channels", value: status?.channels.targets || 0, color: "text-violet-400" },
          { label: "Tasks", value: status?.tasks.pending || 0, color: "text-cyan-400" },
        ].map((s) => (
          <div key={s.label} className="glass-card p-4 text-center">
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-gray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Workflow Templates */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Automation Workflows</h3>
        <div className="grid grid-cols-2 gap-4">
          {WORKFLOW_TEMPLATES.map((tpl) => (
            <div key={tpl.id} className="glass-card p-5 hover:border-blue-500/40 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${tpl.color} flex items-center justify-center text-2xl`}>
                    {tpl.icon}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{tpl.name}</div>
                    <div className="text-xs text-gray-500 mt-1">{tpl.desc}</div>
                  </div>
                </div>
                <button
                  onClick={() => createAndStartWorkflow(tpl.id)}
                  className="btn-primary text-xs"
                >
                  Launch
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Active Workflows */}
      {workflows.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Active Workflows</h3>
          <div className="space-y-3">
            {workflows.map((wf) => (
              <div key={wf.id} className="glass-card p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">{wf.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Step {wf.current_step}/{wf.total_steps} • {wf.status}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {wf.status === "running" && (
                      <span className="badge badge-active animate-pulse-slow">Running</span>
                    )}
                    {wf.status === "completed" && (
                      <span className="badge badge-active">Completed</span>
                    )}
                    {wf.status === "paused" && (
                      <span className="badge badge-warming">Paused</span>
                    )}
                  </div>
                </div>
                <div className="progress-bar mt-3">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${(wf.current_step / wf.total_steps) * 100}%`, background: "linear-gradient(90deg, #3b82f6, #8b5cf6)" }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Task Queue */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Task Queue</h3>
        <p className="text-xs text-gray-600">
          Enqueue tasks for autonomous processing: POST to <code className="text-blue-400">/api/v1/agent/tasks/enqueue</code>
        </p>
        <div className="mt-3 grid grid-cols-5 gap-2">
          {["import_accounts", "warm", "comment", "parse_channels", "boost"].map((task) => (
            <button
              key={task}
              onClick={async () => {
                await fetch(`${API}/agent/tasks/enqueue?task_type=${task}&priority=3`, { method: "POST" });
                load();
              }}
              className="btn-ghost text-xs py-2"
            >
              + {task.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
