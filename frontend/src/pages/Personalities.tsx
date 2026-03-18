import { useEffect, useState } from "react";

const API = "/api/v1";

interface Personality {
  id: string;
  name: string;
  tone: string;
  use_case: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
}

const DEFAULT_PERSONALITIES = [
  { name: "Hater", tone: "Critical, dismissive, arrogant", use_case: "Provokes clicks from curious readers", system_prompt: "You are a skeptical Telegram user. Write a short critical comment. Be blunt. 15-30 words.", temperature: 0.8, max_tokens: 50 },
  { name: "Expert", tone: "Knowledgeable, helpful", use_case: "Crypto, finance, education channels", system_prompt: "You are an expert. Add a helpful insight. Sound knowledgeable. 15-35 words.", temperature: 0.6, max_tokens: 60 },
  { name: "Questioner", tone: "Curious, engaging", use_case: "Increases comment thread activity", system_prompt: "You are curious. Ask an interesting question about this post. 10-25 words.", temperature: 0.75, max_tokens: 40 },
  { name: "Controversial", tone: "Polarizing opinion", use_case: "Drives debate and profile clicks", system_prompt: "You have a strong controversial opinion. State it boldly. 15-30 words.", temperature: 0.85, max_tokens: 50 },
  { name: "Supportive", tone: "Agreeable, encouraging", use_case: "Builds positive presence", system_prompt: "You strongly agree. Write a supportive comment. 10-25 words.", temperature: 0.7, max_tokens: 40 },
  { name: "Flirty", tone: "Playful, suggestive", use_case: "18+ channels, dating niches", system_prompt: "You are flirty. Write a playful, charming comment. 15-30 words.", temperature: 0.9, max_tokens: 50 },
];

export default function Personalities() {
  const [personalities, setPersonalities] = useState<any[]>(DEFAULT_PERSONALITIES);
  const [selected, setSelected] = useState<any | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [testPost, setTestPost] = useState("");
  const [newPersonality, setNewPersonality] = useState({
    name: "", tone: "", use_case: "", system_prompt: "", temperature: 0.7, max_tokens: 50,
    emoji_usage: "sometimes", vocabulary: "moderate", sentence_style: "varied",
    typo_rate: 0.03, abbreviation_tendency: 0.5, age_range: "25-34", nationality: "american",
  });

  const addPersonality = () => {
    if (!newPersonality.name || !newPersonality.system_prompt) return;
    setPersonalities(prev => [...prev, { ...newPersonality, id: `custom-${Date.now()}`, is_active: true }]);
    setNewPersonality({ name: "", tone: "", use_case: "", system_prompt: "", temperature: 0.7, max_tokens: 50, emoji_usage: "sometimes", vocabulary: "moderate", sentence_style: "varied", typo_rate: 0.03, abbreviation_tendency: 0.5, age_range: "25-34", nationality: "american" });
    setShowAdd(false);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Personalities</h1>
          <div className="caption" style={{ marginTop: "4px" }}>{personalities.length} personalities — controls how AI generates comments</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(!showAdd)}>+ Add Personality</button>
      </div>

      {/* Add New Personality */}
      {showAdd && (
        <div className="surface-static" style={{ padding: "20px", marginBottom: "20px" }}>
          <div className="section-title" style={{ marginBottom: "12px" }}>New Personality</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Name</label>
              <input className="input" placeholder="e.g., Crypto Expert" value={newPersonality.name} onChange={e => setNewPersonality({ ...newPersonality, name: e.target.value })} /></div>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Tone</label>
              <input className="input" placeholder="e.g., Confident, analytical" value={newPersonality.tone} onChange={e => setNewPersonality({ ...newPersonality, tone: e.target.value })} /></div>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Use Case</label>
              <input className="input" placeholder="e.g., Crypto channels" value={newPersonality.use_case} onChange={e => setNewPersonality({ ...newPersonality, use_case: e.target.value })} /></div>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Age Range</label>
              <select className="input" value={newPersonality.age_range} onChange={e => setNewPersonality({ ...newPersonality, age_range: e.target.value })}>
                <option>18-24</option><option>25-34</option><option>35-44</option><option>45+</option>
              </select></div>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Vocabulary</label>
              <select className="input" value={newPersonality.vocabulary} onChange={e => setNewPersonality({ ...newPersonality, vocabulary: e.target.value })}>
                <option>simple</option><option>moderate</option><option>advanced</option>
              </select></div>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Emoji Usage</label>
              <select className="input" value={newPersonality.emoji_usage} onChange={e => setNewPersonality({ ...newPersonality, emoji_usage: e.target.value })}>
                <option>never</option><option>rare</option><option>sometimes</option><option>often</option>
              </select></div>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Temperature ({newPersonality.temperature})</label>
              <input className="input" type="range" min="0.3" max="1.2" step="0.05" value={newPersonality.temperature} onChange={e => setNewPersonality({ ...newPersonality, temperature: parseFloat(e.target.value) })} /></div>
            <div><label className="caption" style={{ display: "block", marginBottom: "4px" }}>Typo Rate ({Math.round(newPersonality.typo_rate * 100)}%)</label>
              <input className="input" type="range" min="0" max="0.1" step="0.01" value={newPersonality.typo_rate} onChange={e => setNewPersonality({ ...newPersonality, typo_rate: parseFloat(e.target.value) })} /></div>
          </div>
          <div style={{ marginBottom: "12px" }}>
            <label className="caption" style={{ display: "block", marginBottom: "4px" }}>System Prompt (personality instructions)</label>
            <textarea className="input" placeholder="Describe how this personality speaks, what they focus on, their mannerisms..." value={newPersonality.system_prompt} onChange={e => setNewPersonality({ ...newPersonality, system_prompt: e.target.value })} style={{ minHeight: "80px" }} />
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-primary" onClick={addPersonality}>Create Personality</button>
            <button className="btn btn-ghost" onClick={() => setShowAdd(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Personality Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
        {personalities.map((p, i) => (
          <div key={p.id || i} className="surface" style={{ cursor: "pointer", padding: "16px" }} onClick={() => setSelected(p)}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "8px" }}>
              <div style={{ fontWeight: 600 }}>{p.name}</div>
              <span className={`badge ${p.is_active !== false ? "badge-active" : "badge-muted"}`}>{p.is_active !== false ? "Active" : "Off"}</span>
            </div>
            <div className="caption" style={{ marginBottom: "8px" }}>{p.tone}</div>
            <div className="caption" style={{ fontSize: "11px", marginBottom: "8px" }}>{p.use_case}</div>
            <div style={{ display: "flex", gap: "12px", fontSize: "11px", color: "var(--text-muted)" }}>
              <span>temp: {p.temperature}</span>
              <span>tokens: {p.max_tokens}</span>
            </div>
            {(p.age_range || p.vocabulary) && (
              <div style={{ display: "flex", gap: "8px", marginTop: "8px", fontSize: "11px" }}>
                {p.age_range && <span className="badge badge-muted">{p.age_range}</span>}
                {p.vocabulary && <span className="badge badge-muted">{p.vocabulary}</span>}
                {p.emoji_usage && <span className="badge badge-muted">emoji: {p.emoji_usage}</span>}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Detail Modal */}
      {selected && (
        <div className="modal-overlay anim-fade" onClick={() => setSelected(null)}>
          <div className="modal-content anim-slide" onClick={e => e.stopPropagation()}>
            <div style={{ padding: "20px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
              <div className="section-title">{selected.name}</div>
              <button className="btn-icon" onClick={() => setSelected(null)}>✕</button>
            </div>
            <div style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
              <div><div className="caption">Tone</div><div>{selected.tone}</div></div>
              <div><div className="caption">Use Case</div><div>{selected.use_case}</div></div>
              <div><div className="caption">System Prompt</div><div className="surface-static" style={{ padding: "12px", fontFamily: "monospace", fontSize: "12px", marginTop: "4px" }}>{selected.system_prompt}</div></div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
                <div><div className="caption">Temperature</div><div style={{ fontWeight: 600 }}>{selected.temperature}</div></div>
                <div><div className="caption">Max Tokens</div><div style={{ fontWeight: 600 }}>{selected.max_tokens}</div></div>
                <div><div className="caption">Typo Rate</div><div style={{ fontWeight: 600 }}>{Math.round((selected.typo_rate || 0.03) * 100)}%</div></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
