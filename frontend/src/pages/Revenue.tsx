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
  const [showAddLink, setShowAddLink] = useState(false);
  const [newLink, setNewLink] = useState({ name: "", url: "", campaign: "" });

  const load = () => {
    Promise.all([
      fetch(`${API}/agent/revenue/summary`).then((r) => r.json()),
      fetch(`${API}/agent/revenue/links`).then((r) => r.json()),
    ])
      .then(([s, l]) => { setSummary(s); setLinks(l); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const addLink = async () => {
    if (!newLink.name || !newLink.url) return;
    const params = new URLSearchParams(newLink);
    await fetch(`${API}/agent/revenue/add-link?${params}`, { method: "POST" });
    setNewLink({ name: "", url: "", campaign: "" });
    setShowAddLink(false);
    load();
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin-slow"></div></div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Revenue & Affiliates</h1>
          <p className="text-gray-500 text-sm mt-1">Track clicks, conversions, and revenue</p>
        </div>
        <button onClick={() => setShowAddLink(!showAddLink)} className="btn-primary text-sm">
          + Add Affiliate Link
        </button>
      </div>

      {/* Revenue Stats */}
      <div className="grid grid-cols-5 gap-4">
        {[
          { label: "Total Revenue", value: `$${summary?.total_revenue || 0}`, color: "from-emerald-500 to-teal-400", icon: "💰" },
          { label: "Total Clicks", value: summary?.total_clicks || 0, color: "from-blue-500 to-cyan-400", icon: "👆" },
          { label: "Conversions", value: summary?.total_conversions || 0, color: "from-violet-500 to-purple-400", icon: "🎯" },
          { label: "Conv. Rate", value: `${summary?.conversion_rate || 0}%`, color: "from-amber-500 to-yellow-400", icon: "📈" },
          { label: "Events Today", value: summary?.events_today || 0, color: "from-pink-500 to-rose-400", icon: "📊" },
        ].map((s) => (
          <div key={s.label} className="glass-card stat-card p-5 relative overflow-hidden">
            <div className={`absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r ${s.color} rounded-t-[16px]`} />
            <div className="text-2xl mb-2">{s.icon}</div>
            <div className="text-2xl font-bold text-white">{s.value}</div>
            <div className="text-xs text-gray-500 uppercase tracking-wider mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Add Link Form */}
      {showAddLink && (
        <div className="glass-card p-5 animate-slide-up">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Add Affiliate Link</h3>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Name</label>
              <input type="text" placeholder="My Product" value={newLink.name}
                onChange={(e) => setNewLink({ ...newLink, name: e.target.value })} className="input-modern" />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Affiliate URL</label>
              <input type="url" placeholder="https://..." value={newLink.url}
                onChange={(e) => setNewLink({ ...newLink, url: e.target.value })} className="input-modern" />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Campaign</label>
              <input type="text" placeholder="spring-sale" value={newLink.campaign}
                onChange={(e) => setNewLink({ ...newLink, campaign: e.target.value })} className="input-modern" />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={addLink} className="btn-success text-sm">Create Link</button>
            <button onClick={() => setShowAddLink(false)} className="btn-ghost text-sm">Cancel</button>
          </div>
        </div>
      )}

      {/* Links Table */}
      <div className="glass-card">
        <div className="p-4 border-b border-white/5">
          <h3 className="text-sm font-semibold text-gray-400">Affiliate Links ({links.length})</h3>
        </div>
        {links.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <div className="text-4xl mb-3">🔗</div>
            <div>No affiliate links yet</div>
            <button onClick={() => setShowAddLink(true)} className="btn-primary text-sm mt-4">+ Add Your First Link</button>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-gray-500 text-xs uppercase">
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Campaign</th>
                <th className="px-4 py-3 text-right">Clicks</th>
                <th className="px-4 py-3 text-right">Conv.</th>
                <th className="px-4 py-3 text-right">Revenue</th>
                <th className="px-4 py-3 text-right">CTR</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link) => (
                <tr key={link.id} className="border-b border-white/5 hover:bg-white/2">
                  <td className="px-4 py-3">
                    <div className="font-medium text-white">{link.name}</div>
                    <div className="text-xs text-gray-600 font-mono truncate max-w-[200px]">{link.url}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{link.campaign}</td>
                  <td className="px-4 py-3 text-right text-blue-400 font-mono">{link.clicks}</td>
                  <td className="px-4 py-3 text-right text-violet-400 font-mono">{link.conversions}</td>
                  <td className="px-4 py-3 text-right text-emerald-400 font-mono font-semibold">${link.revenue.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-gray-400">
                    {link.clicks > 0 ? ((link.conversions / link.clicks) * 100).toFixed(1) : "0.0"}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Budget Section */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-gray-400 mb-4">Budget Management</h3>
        <p className="text-xs text-gray-600 mb-3">
          Control spending limits per category. API: <code className="text-blue-400">/api/v1/agent/budget/status</code>
        </p>
        <div className="grid grid-cols-4 gap-3">
          {["proxies", "accounts", "ai", "total"].map((cat) => (
            <div key={cat} className="glass-card p-3">
              <div className="text-xs text-gray-500 uppercase mb-2">{cat}</div>
              <div className="text-lg font-bold text-white">$0</div>
              <div className="text-xs text-gray-600">of $1000/mo</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
