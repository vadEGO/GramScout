import { useEffect, useState } from "react";

const API = "/api/v1";

const TABS = [
  { id: "general", label: "General" },
  { id: "automation", label: "Automation" },
  { id: "llm", label: "AI Models" },
  { id: "troubleshoot", label: "Troubleshoot" },
];

export default function Settings() {
  const [activeTab, setActiveTab] = useState("general");
  const [saved, setSaved] = useState(false);

  const [env, setEnv] = useState({
    TELEGRAM_API_ID: "", TELEGRAM_API_HASH: "", OPENROUTER_API_KEY: "",
    SECRET_KEY: "", ENCRYPTION_KEY: "",
  });

  const [automation, setAutomation] = useState({
    MAX_ACCOUNTS_PER_PROXY: "5", DEFAULT_COMMENT_DELAY_MIN: "30",
    DEFAULT_COMMENT_DELAY_MAX: "300", MAX_CONCURRENT_WORKERS: "50",
    WARMING_ACTIONS_PER_HOUR: "5", WARMING_SESSION_DURATION_MIN: "15",
  });

  const [providers, setProviders] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [roles, setRoles] = useState<Record<string, any>>({});
  const [checkResult, setCheckResult] = useState<any>(null);
  const [diagnosis, setDiagnosis] = useState("");
  const [diagnoseQuery, setDiagnoseQuery] = useState("Analyze the system and identify any issues");
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState<Record<string, string>>({});
  const [showAddProvider, setShowAddProvider] = useState(false);
  const [newProvider, setNewProvider] = useState({ name: "", type: "openrouter", api_key: "" });
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    if (activeTab === "llm") {
      Promise.all([
        fetch(`${API}/llm/providers`).then(r => r.json()).catch(() => []),
        fetch(`${API}/llm/models`).then(r => r.json()).catch(() => []),
        fetch(`${API}/llm/models/roles`).then(r => r.json()).catch(() => ({})),
      ]).then(([p, m, r]) => { setProviders(p); setModels(m); setRoles(r); });
    }
  }, [activeTab]);

  const downloadEnv = () => {
    const all = { ...env, ...automation };
    const blob = new Blob([Object.entries(all).map(([k, v]) => `${k}=${v}`).join("\n")], { type: "text/plain" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = ".env"; a.click();
    setSaved(true);
  };

  const addProvider = async () => {
    const params = new URLSearchParams(newProvider);
    await fetch(`${API}/llm/providers?${params}`, { method: "POST" });
    setShowAddProvider(false);
  };

  const runQuickCheck = async () => {
    setRunning(true);
    const res = await fetch(`${API}/troubleshoot/quick-check`, { method: "POST" });
    setCheckResult(await res.json());
    setRunning(false);
  };

  const runDiagnosis = async () => {
    setRunning(true); setDiagnosis("Analyzing...");
    const params = new URLSearchParams({ query: diagnoseQuery });
    const res = await fetch(`${API}/troubleshoot/analyze?${params}`, { method: "POST" });
    const data = await res.json();
    setDiagnosis(data.diagnosis || data.message || `Status: ${data.status}`);
    setRunning(false);
  };

  const viewLogs = async (svc: string) => {
    const res = await fetch(`${API}/troubleshoot/logs/${svc}`);
    const data = await res.json();
    setLogs(prev => ({ ...prev, [svc]: data.logs }));
  };

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: "20px" }}>Settings</h1>

      <div className="tabs">
        {TABS.map(tab => (
          <div key={tab.id} className={`tab ${activeTab === tab.id ? "active" : ""}`} onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </div>
        ))}
      </div>

      {activeTab === "general" && (
        <div className="surface-static" style={{ padding: "24px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>API Keys & Credentials</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {[
              { key: "TELEGRAM_API_ID", label: "Telegram API ID", ph: "From my.telegram.org/apps" },
              { key: "TELEGRAM_API_HASH", label: "Telegram API Hash", ph: "From my.telegram.org/apps" },
              { key: "OPENROUTER_API_KEY", label: "OpenRouter API Key", ph: "sk-or-v1-..." },
              { key: "SECRET_KEY", label: "App Secret Key", ph: "Random string" },
              { key: "ENCRYPTION_KEY", label: "Encryption Key", ph: "For session encryption" },
            ].map(({ key, label, ph }) => (
              <div key={key}>
                <label className="caption" style={{ display: "block", marginBottom: "4px" }}>{label}</label>
                <input className="input" type="password" placeholder={ph} value={(env as any)[key] || ""} onChange={e => setEnv({ ...env, [key]: e.target.value })} />
              </div>
            ))}
          </div>
          <button className="btn btn-primary" style={{ marginTop: "16px" }} onClick={downloadEnv}>Download .env</button>
          {saved && <span style={{ color: "var(--green)", marginLeft: "8px", fontSize: "12px" }}>✅ Saved</span>}
        </div>
      )}

      {activeTab === "automation" && (
        <div className="surface-static" style={{ padding: "24px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>Automation Settings</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            {[
              { key: "MAX_ACCOUNTS_PER_PROXY", label: "Max Accounts per Proxy" },
              { key: "DEFAULT_COMMENT_DELAY_MIN", label: "Comment Delay Min (sec)" },
              { key: "DEFAULT_COMMENT_DELAY_MAX", label: "Comment Delay Max (sec)" },
              { key: "MAX_CONCURRENT_WORKERS", label: "Max Concurrent Workers" },
              { key: "WARMING_ACTIONS_PER_HOUR", label: "Warming Actions/Hour" },
              { key: "WARMING_SESSION_DURATION_MIN", label: "Warming Session (min)" },
            ].map(({ key, label }) => (
              <div key={key}>
                <label className="caption" style={{ display: "block", marginBottom: "4px" }}>{label}</label>
                <input className="input" type="number" value={(automation as any)[key]} onChange={e => setAutomation({ ...automation, [key]: e.target.value })} />
              </div>
            ))}
          </div>
          <button className="btn btn-primary" style={{ marginTop: "16px" }} onClick={downloadEnv}>Download .env</button>
        </div>
      )}

      {activeTab === "llm" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="surface-static" style={{ padding: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
              <div className="section-title">LLM Providers</div>
              <button className="btn btn-primary btn-sm" onClick={() => setShowAddProvider(!showAddProvider)}>+ Add Provider</button>
            </div>
            {showAddProvider && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px", marginBottom: "12px" }}>
                <input className="input" placeholder="Provider name" value={newProvider.name} onChange={e => setNewProvider({ ...newProvider, name: e.target.value })} />
                <select className="input" value={newProvider.type} onChange={e => setNewProvider({ ...newProvider, type: e.target.value })}>
                  <option value="openrouter">OpenRouter</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="google">Google AI</option>
                </select>
                <input className="input" type="password" placeholder="API Key" value={newProvider.api_key} onChange={e => setNewProvider({ ...newProvider, api_key: e.target.value })} />
                <div style={{ gridColumn: "1 / -1", display: "flex", gap: "8px" }}>
                  <button className="btn btn-primary btn-sm" onClick={addProvider}>Add</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setShowAddProvider(false)}>Cancel</button>
                </div>
              </div>
            )}
            {providers.length === 0 ? (
              <div className="caption">No providers configured</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Name</th><th>Type</th><th>Key</th><th>Daily Spend</th></tr></thead>
                  <tbody>{providers.map(p => (
                    <tr key={p.id}><td style={{ fontWeight: 500 }}>{p.name}</td><td>{p.type}</td><td><span className={p.has_api_key ? "badge badge-active" : "badge badge-danger"}>{p.has_api_key ? "✓" : "✗"}</span></td><td>${p.daily_spend.toFixed(2)}</td></tr>
                  ))}</tbody>
                </table>
              </div>
            )}
          </div>

          <div className="surface-static" style={{ padding: "20px" }}>
            <div className="section-title" style={{ marginBottom: "12px" }}>Available Models ({models.length})</div>
            <div style={{ maxHeight: "200px", overflowY: "auto" }}>
              {models.map((m: any) => (
                <div key={m.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
                  <span>{m.display_name} <span className="caption">{m.provider}</span></span>
                  <span style={{ fontSize: "12px" }}>
                    <span style={{ color: m.quality_score >= 8 ? "var(--green)" : "var(--text-muted)" }}>Q:{m.quality_score}</span>
                    {" "}<span style={{ color: m.speed_score >= 8 ? "var(--green)" : "var(--text-muted)" }}>S:{m.speed_score}</span>
                    {" "}<span className="caption">${m.cost_per_1m_input}/${m.cost_per_1m_output}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "troubleshoot" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="surface-static" style={{ padding: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
              <div className="section-title">Quick Health Check</div>
              <button className="btn btn-primary btn-sm" onClick={runQuickCheck} disabled={running}>
                {running ? "Checking..." : "Run Check"}
              </button>
            </div>
            {checkResult && (
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <div className={`alert ${checkResult.healthy ? "alert-ok" : "alert-error"}`}>
                  {checkResult.healthy ? "✅ System Healthy" : `❌ ${checkResult.issues.length} Issue(s)`}
                </div>
                {checkResult.issues.map((i: string, idx: number) => (
                  <div key={idx} className="alert alert-error" style={{ fontSize: "12px" }}>🔴 {i}</div>
                ))}
                {checkResult.warnings.map((w: string, idx: number) => (
                  <div key={idx} className="alert alert-warn" style={{ fontSize: "12px" }}>⚠️ {w}</div>
                ))}
              </div>
            )}
          </div>

          <div className="surface-static" style={{ padding: "20px" }}>
            <div className="section-title" style={{ marginBottom: "12px" }}>AI Diagnosis</div>
            <textarea className="input" value={diagnoseQuery} onChange={e => setDiagnoseQuery(e.target.value)} style={{ minHeight: "60px", marginBottom: "8px" }} />
            <button className="btn btn-primary btn-sm" onClick={runDiagnosis} disabled={running}>
              {running ? "Analyzing..." : "🔍 Analyze"}
            </button>
            {diagnosis && (
              <div style={{ marginTop: "12px", padding: "12px", background: "var(--bg)", borderRadius: "8px", fontSize: "12px", fontFamily: "monospace", whiteSpace: "pre-wrap" }}>
                {diagnosis}
              </div>
            )}
          </div>

          <div className="surface-static" style={{ padding: "20px" }}>
            <div className="section-title" style={{ marginBottom: "12px" }}>Service Logs</div>
            <div style={{ display: "flex", gap: "6px", marginBottom: "12px" }}>
              {["backend", "frontend", "postgres", "redis"].map(svc => (
                <button key={svc} className="btn btn-ghost btn-sm" onClick={() => viewLogs(svc)}>{svc}</button>
              ))}
            </div>
            {Object.entries(logs).map(([svc, log]) => (
              <div key={svc} style={{ marginBottom: "12px" }}>
                <div className="caption">{svc}:</div>
                <div style={{ background: "var(--bg)", borderRadius: "8px", padding: "12px", fontSize: "11px", fontFamily: "monospace", maxHeight: "200px", overflowY: "auto", whiteSpace: "pre-wrap", color: "var(--text-secondary)" }}>
                  {log}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
