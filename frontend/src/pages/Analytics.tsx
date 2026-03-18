import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const API = "/api/v1";

interface BanRate {
  total_accounts: number;
  banned: number;
  ban_rate_pct: number;
}

export default function Analytics() {
  const [banRate, setBanRate] = useState<BanRate | null>(null);
  const [actionData, setActionData] = useState<any[]>([]);
  const [hours, setHours] = useState(24);

  const load = () => {
    Promise.all([
      fetch(`${API}/analytics/ban-rate`).then(r => r.json()),
      fetch(`${API}/analytics/actions?hours=${hours}`).then(r => r.json()),
    ]).then(([br, ad]) => {
      setBanRate(br);
      setActionData(Object.entries(ad.actions || {}).map(([name, count]) => ({ name, count })));
    }).catch(console.error);
  };

  useEffect(() => { load(); }, [hours]);

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: "24px" }}>Analytics</h1>

      {/* KPIs */}
      {banRate && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "24px" }}>
          <div className="card-compact" style={{ padding: "20px" }}>
            <div className="kpi-number">{banRate.total_accounts}</div>
            <div className="kpi-label">Total Accounts</div>
          </div>
          <div className="card-compact" style={{ padding: "20px" }}>
            <div className="kpi-number" style={{ color: "var(--danger)" }}>{banRate.banned}</div>
            <div className="kpi-label">Banned</div>
          </div>
          <div className="card-compact" style={{ padding: "20px" }}>
            <div className="kpi-number" style={{ color: banRate.ban_rate_pct > 10 ? "var(--danger)" : banRate.ban_rate_pct > 5 ? "var(--warning)" : "var(--success)" }}>
              {banRate.ban_rate_pct}%
            </div>
            <div className="kpi-label">Ban Rate</div>
          </div>
        </div>
      )}

      {/* Time range selector */}
      <div style={{ display: "flex", gap: "4px", marginBottom: "16px" }}>
        {[6, 12, 24, 48, 168].map(h => (
          <button key={h} onClick={() => setHours(h)}
            className={`btn btn-sm ${hours === h ? "btn-primary" : "btn-ghost"}`}>
            {h}h
          </button>
        ))}
      </div>

      {/* Actions Chart */}
      <div className="card">
        <div className="section-title" style={{ fontSize: "14px", marginBottom: "16px" }}>
          Actions (Last {hours}h)
        </div>
        {actionData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={actionData}>
              <XAxis dataKey="name" stroke="#9CA3AF" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#9CA3AF" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: "8px", fontSize: "12px" }} />
              <Bar dataKey="count" fill="#2563EB" radius={[6, 6, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: "center", padding: "48px", color: "var(--text-muted)" }}>
            No actions recorded in this period
          </div>
        )}
      </div>
    </div>
  );
}
