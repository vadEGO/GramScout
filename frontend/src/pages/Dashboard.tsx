import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const API = "/api/v1";

interface DashboardData {
  total_accounts: number;
  active_accounts: number;
  banned_accounts: number;
  comments_today: number;
  reactions_today: number;
}

const PIE_COLORS = ["#4F46E5", "#22C55E", "#EF4444"];

function SkeletonCard() {
  return (
    <div>
      <div className="skeleton" style={{ width: "60px", height: "28px", marginBottom: "6px" }} />
      <div className="skeleton" style={{ width: "80px", height: "10px" }} />
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    fetch(`${API}/analytics/dashboard`)
      .then((r) => r.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div>
        <div className="skeleton" style={{ width: "180px", height: "24px", marginBottom: "32px" }} />
        <div className="grid-6" style={{ display: "grid", gap: "16px", marginBottom: "32px" }}>
          {[1,2,3,4,5,6].map(i => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (!data) return <div style={{ color: "var(--red)" }}>Failed to load</div>;

  const survivalRate = data.total_accounts > 0
    ? Math.round(((data.total_accounts - data.banned_accounts) / data.total_accounts) * 100)
    : 100;

  const kpis = [
    { label: "Total Accounts", value: data.total_accounts },
    { label: "Active", value: data.active_accounts },
    { label: "Banned", value: data.banned_accounts },
    { label: "Comments Today", value: data.comments_today },
    { label: "Reactions Today", value: data.reactions_today },
    { label: "Survival Rate", value: `${survivalRate}%` },
  ];

  const pieData = [
    { name: "Active", value: data.active_accounts },
    { name: "Other", value: Math.max(0, data.total_accounts - data.active_accounts - data.banned_accounts) },
    { name: "Banned", value: data.banned_accounts },
  ].filter(d => d.value > 0);

  const barData = [
    { name: "Comments", count: data.comments_today },
    { name: "Reactions", count: data.reactions_today },
  ];

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: "28px" }}>Dashboard</h1>

      {/* KPI Row - responsive */}
      <div className="grid-6" style={{ display: "grid", gap: "16px", marginBottom: "32px" }}>
        {kpis.map(kpi => (
          <div key={kpi.label}>
            <div className="kpi-value">{kpi.value}</div>
            <div className="kpi-label">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Charts - responsive */}
      <div className="grid-2" style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "16px" }}>
        <div className="surface-static" style={{ padding: "20px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>Account Distribution</div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" stroke="none">
                {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "var(--surface-solid)", border: "1px solid var(--border)", borderRadius: "10px", fontSize: "12px" }} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", justifyContent: "center", gap: "16px", marginTop: "8px" }}>
            {pieData.map((d, i) => (
              <div key={d.name} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: PIE_COLORS[i], display: "inline-block" }} />
                <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="surface-static" style={{ padding: "20px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>Today's Activity</div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={barData} barSize={36}>
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "var(--surface-solid)", border: "1px solid var(--border)", borderRadius: "10px", fontSize: "12px" }} />
              <Bar dataKey="count" fill="var(--accent)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Health - responsive */}
      <div style={{ marginTop: "24px" }}>
        <div className="section-title" style={{ marginBottom: "12px" }}>System Health</div>
        <div className="grid-4" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px" }}>
          {[
            { label: "Survival Rate", value: `${survivalRate}%`, good: survivalRate > 90 },
            { label: "Active Sessions", value: data.active_accounts, good: true },
            { label: "Comments (24h)", value: data.comments_today, good: null },
            { label: "Reactions (24h)", value: data.reactions_today, good: null },
          ].map(item => (
            <div key={item.label} className="surface-static" style={{ padding: "14px 16px" }}>
              <div className="kpi-label">{item.label}</div>
              <div style={{
                fontSize: "20px", fontWeight: 700, letterSpacing: "-0.03em",
                color: item.good === true ? "var(--green)" : item.good === false ? "var(--red)" : "var(--text)",
              }}>
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
