import { useEffect, useState } from "react";

const API = "/api/v1";

interface Account { id: string; phone: string; status: string; warming_stage: number; }

export default function Warming() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [engineStatus, setEngineStatus] = useState("idle");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const load = () => {
    setLoading(true);
    fetch(`${API}/accounts`).then(r => r.json()).then(setAccounts).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const startWarming = async () => {
    await fetch(`${API}/warming/start`, { method: "POST" });
    setEngineStatus("running");
  };

  const stopWarming = async () => {
    await fetch(`${API}/warming/stop`, { method: "POST" });
    setEngineStatus("stopped");
  };

  const warmSelected = async () => {
    const params = Array.from(selectedIds).map(id => `account_ids=${id}`).join("&");
    await fetch(`${API}/warming/accounts?${params}`, { method: "POST" });
    setSelectedIds(new Set());
    load();
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedIds(next);
  };

  const warmingNow = accounts.filter(a => a.status === "warming");

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: "24px" }}>Warming Engine</h1>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "20px" }}>
        <div className="surface-static" style={{ padding: "16px" }}>
          <div className="kpi-label">Engine Status</div>
          <div style={{ fontSize: "18px", fontWeight: 700, color: engineStatus === "running" ? "var(--green)" : "var(--text-secondary)" }}>{engineStatus}</div>
        </div>
        <div className="surface-static" style={{ padding: "16px" }}>
          <div className="kpi-label">Warming Now</div>
          <div className="kpi-value" style={{ color: "var(--amber)" }}>{warmingNow.length}</div>
        </div>
        <div className="surface-static" style={{ padding: "16px" }}>
          <div className="kpi-label">Total Accounts</div>
          <div className="kpi-value">{accounts.length}</div>
        </div>
        <div className="surface-static" style={{ padding: "16px" }}>
          <div className="kpi-label">Selected</div>
          <div className="kpi-value" style={{ color: "var(--accent)" }}>{selectedIds.size}</div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        <button className="btn btn-primary" onClick={startWarming} disabled={engineStatus === "running"}>Start Engine</button>
        <button className="btn btn-danger" onClick={stopWarming} disabled={engineStatus !== "running"}>Stop Engine</button>
        <button className="btn btn-secondary" onClick={warmSelected} disabled={selectedIds.size === 0}>Warm Selected ({selectedIds.size})</button>
        <button className="btn btn-ghost" onClick={load} style={{ marginLeft: "auto" }}>Refresh</button>
      </div>

      {accounts.length === 0 ? (
        <div className="surface-static" style={{ textAlign: "center", padding: "40px" }}>
          <div className="caption">No accounts to warm</div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th><input type="checkbox" onChange={() => setSelectedIds(selectedIds.size === accounts.length ? new Set() : new Set(accounts.map(a => a.id)))} checked={selectedIds.size === accounts.length && accounts.length > 0} /></th><th>Phone</th><th>Status</th><th>Warming Stage</th></tr></thead>
            <tbody>
              {accounts.map(acc => (
                <tr key={acc.id}>
                  <td><input type="checkbox" checked={selectedIds.has(acc.id)} onChange={() => toggleSelect(acc.id)} /></td>
                  <td style={{ fontFamily: "monospace" }}>{acc.phone}</td>
                  <td><span className={`badge ${acc.status === "warming" ? "badge-warning" : acc.status === "active" ? "badge-active" : acc.status === "banned" ? "badge-danger" : "badge-muted"}`}>{acc.status}</span></td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div className="progress-track" style={{ width: "120px" }}>
                        <div className="progress-fill" style={{ width: `${acc.warming_stage}%`, background: acc.warming_stage >= 80 ? "var(--green)" : acc.warming_stage >= 50 ? "var(--amber)" : "var(--accent)" }} />
                      </div>
                      <span className="caption">{acc.warming_stage}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
