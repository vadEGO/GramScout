import { useEffect, useState } from "react";

const API = "/api/v1";

interface DashboardData {
  total_accounts: number;
  active_accounts: number;
  banned_accounts: number;
  comments_today: number;
  reactions_today: number;
}

function Sparkline({ points }: { points: number[] }) {
  const max = Math.max(...points);
  const min = Math.min(...points);

  const normalized = points.map((point, index) => {
    const x = (index / (points.length - 1)) * 100;
    const y = max === min ? 50 : 100 - ((point - min) / (max - min)) * 100;
    return `${x},${y}`;
  });

  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: "70px" }}>
      <polyline
        points={normalized.join(" ")}
        fill="none"
        stroke="var(--text)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
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
        <div className="dashboard-headline">GRAMSCOUT</div>
        <div className="dashboard-subtitle">DASHBOARD</div>
        <div className="grid-2" style={{ display: "grid", gap: "16px", marginTop: "28px" }}>
          {[1, 2, 3, 4].map((item) => (
            <div key={item} className="metric-card">
              <div className="skeleton" style={{ width: "120px", marginBottom: "12px" }} />
              <div className="skeleton" style={{ width: "160px", height: "38px", marginBottom: "16px" }} />
              <div className="skeleton" style={{ width: "100%", height: "70px" }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data) return <div style={{ color: "var(--red)" }}>Failed to load dashboard.</div>;

  const metrics = [
    {
      label: "TOTAL SUBSCRIBERS",
      value: data.total_accounts.toLocaleString(),
      points: [12, 34, 22, 56, 48, 51, 39, 62],
    },
    {
      label: "ACTIVE GROWTH",
      value: `${Math.max(0, Math.round((data.active_accounts / Math.max(data.total_accounts, 1)) * 100))}%`,
      points: [8, 20, 17, 43, 29, 38, 42, 57],
    },
    {
      label: "MESSAGES SENT",
      value: data.comments_today.toLocaleString(),
      points: [10, 15, 14, 33, 29, 24, 18, 33],
    },
    {
      label: "AI ENGAGEMENT",
      value: `${Math.max(0, Math.min(100, Math.round((data.reactions_today / Math.max(data.comments_today, 1)) * 100)))}%`,
      points: [9, 25, 17, 41, 33, 46, 24, 44],
    },
  ];

  const activity = [
    `10:45 AM - ${data.active_accounts} agents currently running`,
    `10:30 AM - ${data.comments_today.toLocaleString()} comments processed today`,
    `10:15 AM - ${data.total_accounts.toLocaleString()} total accounts tracked`,
    `09:50 AM - ${data.reactions_today.toLocaleString()} reactions generated today`,
  ];

  return (
    <div>
      <div className="dashboard-headline">GRAMSCOUT</div>
      <div className="dashboard-subtitle">DASHBOARD</div>

      <div className="grid-2" style={{ display: "grid", gap: "16px", marginTop: "28px" }}>
        {metrics.map((metric) => (
          <section key={metric.label} className="metric-card">
            <div className="metric-card-label">{metric.label}</div>
            <div className="metric-card-value">{metric.value}</div>
            <Sparkline points={metric.points} />
          </section>
        ))}
      </div>

      <section className="activity-panel" style={{ marginTop: "20px" }}>
        <div className="metric-card-label" style={{ marginBottom: "16px" }}>
          RECENT ACTIVITY
        </div>
        <div style={{ display: "grid", gap: "12px" }}>
          {activity.map((entry) => (
            <div key={entry} className="activity-line">
              {entry}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
