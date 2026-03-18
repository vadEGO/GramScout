import { useEffect, useState } from "react";

const API = "/api/v1";

interface RevenueSummary {
  total_links: number;
  total_clicks: number;
  total_conversions: number;
  total_revenue: number;
  conversion_rate: number;
  events_today: number;
}

interface AffiliateLink {
  id: string;
  name: string;
  url: string;
  campaign: string;
  clicks: number;
  conversions: number;
  revenue: number;
}

export default function Revenue() {
  const [summary, setSummary] = useState<RevenueSummary | null>(null);
  const [links, setLinks] = useState<AffiliateLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newLink, setNewLink] = useState({ name: "", url: "", campaign: "" });

  const load = () => {
    Promise.all([
      fetch(`${API}/agent/revenue/summary`).then(r => r.json()),
      fetch(`${API}/agent/revenue/links`).then(r => r.json()),
    ]).then(([s, l]) => { setSummary(s); setLinks(l); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const addLink = async () => {
    if (!newLink.name || !newLink.url) return;
    await fetch(`${API}/agent/revenue/add-link?${new URLSearchParams(newLink)}`, { method: "POST" });
    setNewLink({ name: "", url: "", campaign: "" });
    setShowAdd(false);
    load();
  };

  if (loading) return <div><div className="skeleton" style={{ width: "200px", height: "24px" }} /></div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Revenue & Affiliates</h1>
          <div className="caption" style={{ marginTop: "4px" }}>Track clicks, conversions, and revenue</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(!showAdd)}>+ Add Link</button>
      </div>

      {/* KPIs */}
      <div className="grid-5" style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "12px", marginBottom: "20px" }}>
        {[
          { label: "Total Revenue", value: `$${summary?.total_revenue || 0}` },
          { label: "Total Clicks", value: summary?.total_clicks || 0 },
          { label: "Conversions", value: summary?.total_conversions || 0 },
          { label: "Conv. Rate", value: `${summary?.conversion_rate || 0}%` },
          { label: "Events Today", value: summary?.events_today || 0 },
        ].map(s => (
          <div key={s.label}>
            <div className="kpi-value" style={{ fontSize: "24px" }}>{s.value}</div>
            <div className="kpi-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Add Link Form */}
      {showAdd && (
        <div className="surface-static" style={{ padding: "16px", marginBottom: "16px" }}>
          <div className="section-title" style={{ marginBottom: "12px" }}>Add Affiliate Link</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px", marginBottom: "8px" }}>
            <input className="input" placeholder="Name" value={newLink.name} onChange={e => setNewLink({ ...newLink, name: e.target.value })} />
            <input className="input" placeholder="URL" value={newLink.url} onChange={e => setNewLink({ ...newLink, url: e.target.value })} />
            <input className="input" placeholder="Campaign" value={newLink.campaign} onChange={e => setNewLink({ ...newLink, campaign: e.target.value })} />
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-primary" onClick={addLink}>Create</button>
            <button className="btn btn-ghost" onClick={() => setShowAdd(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Links Table */}
      {links.length === 0 ? (
        <div className="surface-static" style={{ textAlign: "center", padding: "40px" }}>
          <div style={{ fontSize: "24px", marginBottom: "8px" }}>🔗</div>
          <div className="caption">No affiliate links yet</div>
          <button className="btn btn-primary" style={{ marginTop: "12px" }} onClick={() => setShowAdd(true)}>+ Add Your First Link</button>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Campaign</th><th>Clicks</th><th>Conv.</th><th>Revenue</th><th>CTR</th></tr></thead>
            <tbody>
              {links.map(link => (
                <tr key={link.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{link.name}</div>
                    <div className="caption" style={{ fontFamily: "monospace", fontSize: "11px" }}>{link.url}</div>
                  </td>
                  <td className="caption">{link.campaign}</td>
                  <td style={{ fontVariantNumeric: "tabular-nums", color: "var(--accent)" }}>{link.clicks}</td>
                  <td style={{ fontVariantNumeric: "tabular-nums", color: "var(--green)" }}>{link.conversions}</td>
                  <td style={{ fontWeight: 600, color: "var(--green)", fontVariantNumeric: "tabular-nums" }}>${link.revenue.toFixed(2)}</td>
                  <td className="caption">{link.clicks > 0 ? ((link.conversions / link.clicks) * 100).toFixed(1) : "0.0"}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Budget */}
      <div style={{ marginTop: "20px" }}>
        <div className="section-title" style={{ marginBottom: "12px" }}>Budget</div>
        <div className="grid-4" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px" }}>
          {["proxies", "accounts", "ai", "total"].map(cat => (
            <div key={cat} className="surface-static" style={{ padding: "12px" }}>
              <div className="kpi-label">{cat}</div>
              <div style={{ fontWeight: 600 }}>$0</div>
              <div className="caption">of $1000/mo</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
