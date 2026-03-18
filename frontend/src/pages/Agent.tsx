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

const TEMPLATES = [
  { id: "full_pipeline", name: "Full Growth Pipeline", desc: "Import → Proxy → Warm → Parse → Comment → React" },
  { id: "quick_boost", name: "Quick Channel Boost", desc: "Use warm accounts to boost a specific channel" },
  { id: "account_recovery", name: "Account Recovery", desc: "Recover and re-warm banned accounts" },
  { id: "revenue_generation", name: "Revenue Generation", desc: "Post affiliate links, track conversions" },
];

export default function Agent() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [pipeline, setPipeline] = useState<any>(null);

  const load = () => {
    Promise.all([
      fetch(`${API}/agent/status`).then(r => r.json()),
      fetch(`${API}/agent/workflows`).then(r => r.json()),
      fetch(`${API}/scalability/pipeline/status`).then(r => r.json()),
    ]).then(([s, w, p]) => { setStatus(s); setWorkflows(w); setPipeline(p); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); const i = setInterval(load, 15000); return () => clearInterval(i); }, []);

  const createAndStart = async (templateId: string) => {
    const res = await fetch(`${API}/agent/workflows/create?template_id=${templateId}`, { method: "POST" });
    const data = await res.json();
    if (data.id) await fetch(`${API}/agent/workflows/${data.id}/start`, { method: "POST" });
    load();
  };

  const togglePipeline = async () => {
    if (pipeline?.running) {
      await fetch(`${API}/scalability/pipeline/stop`, { method: "POST" });
    } else {
      await fetch(`${API}/scalability/pipeline/start`, { method: "POST" });
      await fetch(`${API}/scalability/anomaly/start`, { method: "POST" });
    }
    load();
  };

  if (loading) return <div><div className="skeleton" style={{ width: "200px", height: "24px", marginBottom: "32px" }} /></div>;

  const readiness = status ? Math.round(
    ((status.accounts.active / Math.max(status.accounts.total, 1)) * 40) +
    (status.channels.targets > 0 ? 30 : 0) +
    (status.accounts.active > 5 ? 30 : (status.accounts.active / 5) * 30)
  ) : 0;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Agent Control</h1>
          <div className="caption" style={{ marginTop: "4px" }}>Autonomous pipeline and workflow management</div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button className={`btn ${pipeline?.running ? "btn-danger" : "btn-primary"}`} onClick={togglePipeline}>
            {pipeline?.running ? "⏹ Stop Pipeline" : "▶ Start Pipeline"}
          </button>
          <button className="btn btn-secondary" onClick={load}>↻ Refresh</button>
        </div>
      </div>

      {/* Readiness */}
      <div className="surface-static" style={{ padding: "20px", marginBottom: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
          <div className="section-title">System Readiness</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: readiness >= 80 ? "var(--green)" : readiness >= 50 ? "var(--amber)" : "var(--red)" }}>
            {readiness}%
          </div>
        </div>
        <div className="progress-track" style={{ height: "6px" }}>
          <div className="progress-fill" style={{ width: `${readiness}%`, background: readiness >= 80 ? "var(--green)" : readiness >= 50 ? "var(--amber)" : "var(--red)" }} />
        </div>
        <div className="grid-4" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", marginTop: "12px" }}>
          {[
            { ok: (status?.accounts.active || 0) > 0, label: "Active Accounts" },
            { ok: (status?.channels.targets || 0) > 0, label: "Target Channels" },
            { ok: status?.can_comment || false, label: "Can Comment" },
            { ok: !status?.needs_warming, label: "Warm Accounts" },
          ].map(item => (
            <div key={item.label} style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: item.ok ? "var(--green)" : "var(--amber)" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: item.ok ? "var(--green)" : "var(--amber)", display: "inline-block" }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid-6" style={{ display: "grid", gap: "12px", marginBottom: "16px" }}>
        {[
          { label: "Total", value: status?.accounts.total || 0 },
          { label: "Active", value: status?.accounts.active || 0 },
          { label: "Warming", value: status?.accounts.warming || 0 },
          { label: "Banned", value: status?.accounts.banned || 0 },
          { label: "Channels", value: status?.channels.targets || 0 },
          { label: "Pending Tasks", value: status?.tasks.pending || 0 },
        ].map(s => (
          <div key={s.label}>
            <div className="kpi-value" style={{ fontSize: "24px" }}>{s.value}</div>
            <div className="kpi-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Pipeline Status */}
      {pipeline && (
        <div className="surface-static" style={{ padding: "16px", marginBottom: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div className="section-title" style={{ fontSize: "13px" }}>Pipeline Agent</div>
              <div className="caption" style={{ marginTop: "4px" }}>{pipeline.current_step || "Idle"}</div>
            </div>
            <span className={`badge ${pipeline.running ? "badge-active" : "badge-muted"}`}>
              {pipeline.running ? "Running" : "Stopped"}
            </span>
          </div>
          {pipeline.stats && (
            <div style={{ display: "flex", gap: "24px", marginTop: "12px", fontSize: "12px", color: "var(--text-secondary)" }}>
              <span>Comments: {pipeline.stats.comments_posted}</span>
              <span>Reactions: {pipeline.stats.reactions_posted}</span>
              <span>Errors: {pipeline.stats.errors}</span>
            </div>
          )}
        </div>
      )}

      {/* Workflow Templates */}
      <div className="section-title" style={{ marginBottom: "12px" }}>Workflow Templates</div>
      <div className="grid-2" style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "12px", marginBottom: "16px" }}>
        {TEMPLATES.map(tpl => (
          <div key={tpl.id} className="surface" style={{ padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: "14px" }}>{tpl.name}</div>
                <div className="caption" style={{ marginTop: "4px" }}>{tpl.desc}</div>
              </div>
              <button className="btn btn-primary btn-sm" onClick={() => createAndStart(tpl.id)}>Launch</button>
            </div>
          </div>
        ))}
      </div>

      {/* Active Workflows */}
      {workflows.length > 0 && (
        <div>
          <div className="section-title" style={{ marginBottom: "12px" }}>Active Workflows</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {workflows.map(wf => (
              <div key={wf.id} className="surface-static" style={{ padding: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontWeight: 500 }}>{wf.name}</div>
                  <span className={`badge ${wf.status === "running" ? "badge-active" : wf.status === "completed" ? "badge-info" : "badge-muted"}`}>
                    {wf.status}
                  </span>
                </div>
                <div className="progress-track" style={{ marginTop: "8px" }}>
                  <div className="progress-fill" style={{ width: `${(wf.current_step / wf.total_steps) * 100}%` }} />
                </div>
                <div className="caption" style={{ marginTop: "4px" }}>Step {wf.current_step}/{wf.total_steps}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
