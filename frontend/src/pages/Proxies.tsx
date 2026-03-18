import { useEffect, useState } from "react";

const API = "/api/v1";

interface Proxy {
  id: string;
  ip: string;
  port: number;
  country: string;
  provider: string;
  protocol: string;
  is_active: boolean;
  ban_rate: number;
}

export default function Proxies() {
  const [proxies, setProxies] = useState<Proxy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ip: "", port: "", username: "", password: "", country: "", provider: "" });

  const load = () => {
    setLoading(true);
    fetch(`${API}/proxies`).then(r => r.json()).then(setProxies).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const addProxy = async () => {
    const params = new URLSearchParams({ ...form, port: form.port });
    await fetch(`${API}/proxies?${params}`, { method: "POST" });
    setShowForm(false);
    setForm({ ip: "", port: "", username: "", password: "", country: "", provider: "" });
    load();
  };

  const deleteProxy = async (id: string) => {
    await fetch(`${API}/proxies/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Proxies</h1>
          <div className="caption" style={{ marginTop: "4px" }}>{proxies.length} configured</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ Add Proxy"}
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "12px" }}>
            {(["ip", "port", "username", "password", "country", "provider"] as const).map(field => (
              <input key={field} className="input" placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
                type={field === "port" ? "number" : "text"}
                value={(form as any)[field]}
                onChange={e => setForm({ ...form, [field]: e.target.value })} />
            ))}
          </div>
          <button className="btn btn-primary" onClick={addProxy}>Create Proxy</button>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: "48px", color: "var(--text-muted)" }}>Loading...</div>
      ) : proxies.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "48px" }}>
          <div style={{ color: "var(--text-secondary)" }}>No proxies configured</div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>IP:Port</th>
                <th>Country</th>
                <th>Provider</th>
                <th>Protocol</th>
                <th>Ban Rate</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {proxies.map(p => (
                <tr key={p.id}>
                  <td style={{ fontFamily: "monospace" }}>{p.ip}:{p.port}</td>
                  <td>{p.country}</td>
                  <td style={{ color: "var(--text-secondary)" }}>{p.provider}</td>
                  <td><span className="caption">{p.protocol}</span></td>
                  <td style={{ color: p.ban_rate > 0.3 ? "var(--danger)" : p.ban_rate > 0.1 ? "var(--warning)" : "var(--success)" }}>
                    {(p.ban_rate * 100).toFixed(0)}%
                  </td>
                  <td>
                    <span className={`badge ${p.is_active ? "badge-active" : "badge-muted"}`}>
                      {p.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-ghost btn-sm" style={{ color: "var(--danger)" }}
                      onClick={() => deleteProxy(p.id)}>Remove</button>
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
