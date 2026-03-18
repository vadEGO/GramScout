import { useState } from "react";

const API = "/api/v1";

export default function ChannelParser() {
  const [config, setConfig] = useState({
    keywords: "", autoSuffixes: "news, chat, official, group, channel",
    minSubscribers: 100, maxSubscribers: 0, onlyOpenComments: true, language: "auto",
  });
  const [results, setResults] = useState<any[]>([]);
  const [parsing, setParsing] = useState(false);
  const [progress, setProgress] = useState(0);

  const startParsing = async () => {
    setParsing(true); setProgress(0); setResults([]);
    const keywords = config.keywords.split(",").map(k => k.trim()).filter(Boolean);
    const suffixes = config.autoSuffixes.split(",").map(k => k.trim()).filter(Boolean);
    const total = keywords.length * (suffixes.length + 1);
    for (let i = 0; i < total; i++) {
      await new Promise(r => setTimeout(r, 300));
      setProgress(Math.round(((i + 1) / total) * 100));
      if (Math.random() > 0.3) {
        const kw = keywords[i % keywords.length] || "sample";
        setResults(prev => [...prev, {
          id: `ch-${prev.length}`, name: `${kw} ${suffixes[i % suffixes.length] || ""}`.trim(),
          username: `${kw}${suffixes[i % suffixes.length] || ""}`.replace(/\s/g, "").toLowerCase(),
          subscribers: Math.floor(Math.random() * 50000) + 100,
          openComments: Math.random() > 0.3, quality: (Math.random() * 8 + 2).toFixed(1),
        }]);
      }
    }
    setParsing(false);
  };

  const addTarget = async (ch: any) => {
    await fetch(`${API}/channels?url=https://t.me/${ch.username}&name=${ch.name}&username=${ch.username}&subscribers=${ch.subscribers}&is_target=true`, { method: "POST" });
    setResults(prev => prev.filter(r => r.id !== ch.id));
  };

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: "24px" }}>Channel Parser</h1>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div className="surface-static" style={{ padding: "24px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>Search Configuration</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Keywords</label>
              <input className="input" placeholder="crypto, trading, defi" value={config.keywords} onChange={e => setConfig({ ...config, keywords: e.target.value })} /></div>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Auto Suffixes</label>
              <input className="input" value={config.autoSuffixes} onChange={e => setConfig({ ...config, autoSuffixes: e.target.value })} /></div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Min Subscribers</label>
                <input className="input" type="number" value={config.minSubscribers} onChange={e => setConfig({ ...config, minSubscribers: parseInt(e.target.value) })} /></div>
              <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Max (0=unlimited)</label>
                <input className="input" type="number" value={config.maxSubscribers} onChange={e => setConfig({ ...config, maxSubscribers: parseInt(e.target.value) })} /></div>
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}>
              <input type="checkbox" checked={config.onlyOpenComments} onChange={e => setConfig({ ...config, onlyOpenComments: e.target.checked })} />
              Only channels with open comments
            </label>
            <button className="btn btn-primary" onClick={startParsing} disabled={parsing || !config.keywords.trim()}>
              {parsing ? `Parsing... ${progress}%` : "Start Parsing"}
            </button>
            {parsing && <div className="progress-track"><div className="progress-fill" style={{ width: `${progress}%` }} /></div>}
          </div>
        </div>

        <div className="surface-static">
          <div style={{ padding: "16px", borderBottom: "1px solid var(--border)" }}>
            <span className="section-title">Results ({results.length})</span>
          </div>
          <div style={{ maxHeight: "500px", overflowY: "auto" }}>
            {results.length === 0 ? (
              <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
                {parsing ? "Searching..." : "Parse results will appear here"}
              </div>
            ) : (
              results.map(ch => (
                <div key={ch.id} style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: "13px" }}>{ch.name}</div>
                    <div className="caption">@{ch.username} • {ch.subscribers.toLocaleString()} subs{ch.openComments && " • 💬 open"}</div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ color: "var(--accent)", fontSize: "12px", fontFamily: "monospace" }}>Q: {ch.quality}</span>
                    <button className="btn btn-primary btn-sm" onClick={() => addTarget(ch)}>+ Add</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
