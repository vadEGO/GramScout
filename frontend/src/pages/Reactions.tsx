import { useState } from "react";

const API = "/api/v1";

export default function Reactions() {
  const [status, setStatus] = useState("idle");
  const [workers, setWorkers] = useState(3);

  const startEngine = async () => {
    setStatus("starting");
    await fetch(`${API}/reactions/start?num_workers=${workers}`, { method: "POST" });
    setStatus("running");
  };

  const stopEngine = async () => {
    await fetch(`${API}/reactions/stop`, { method: "POST" });
    setStatus("stopped");
  };

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: "24px" }}>Mass Reactions Engine</h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div className="surface-static" style={{ padding: "24px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>Engine Control</div>
          <div style={{ marginBottom: "16px" }}>
            <label className="caption" style={{ display: "block", marginBottom: "8px" }}>Reactor Workers</label>
            <input type="range" min="1" max="20" value={workers} onChange={e => setWorkers(parseInt(e.target.value))} style={{ width: "100%" }} />
            <span style={{ fontSize: "13px", color: "var(--accent)", fontWeight: 600 }}>{workers} workers</span>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-primary" onClick={startEngine} disabled={status === "running"}>Start Reactions</button>
            <button className="btn btn-danger" onClick={stopEngine} disabled={status !== "running"}>Stop Reactions</button>
          </div>
          <div style={{ marginTop: "12px", fontSize: "13px" }}>
            Status: <span style={{ color: status === "running" ? "var(--green)" : "var(--text-secondary)", fontWeight: 600 }}>{status}</span>
          </div>
        </div>

        <div className="surface-static" style={{ padding: "24px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>Reaction Emojis</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
            {["👍", "❤️", "🔥", "😂", "😮", "🎉", "👏", "💯", "🤔", "😢"].map(e => (
              <span key={e} style={{ fontSize: "28px", cursor: "pointer" }}>{e}</span>
            ))}
          </div>
          <p className="caption" style={{ marginTop: "16px" }}>
            Reactions are randomly selected. Lower risk than commenting — generates profile visits from notification clicks.
          </p>
        </div>
      </div>
    </div>
  );
}
