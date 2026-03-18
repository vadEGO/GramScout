import { useState } from "react";

const API = "/api/v1";

export default function Commenting() {
  const [status, setStatus] = useState("idle");
  const [workers, setWorkers] = useState(5);
  const [queueSize, setQueueSize] = useState<number | null>(null);

  const startEngine = async () => {
    setStatus("starting");
    try {
      await fetch(`${API}/commenting/start?num_workers=${workers}`, { method: "POST" });
      setStatus("running");
    } catch { setStatus("error"); }
  };

  const stopEngine = async () => {
    await fetch(`${API}/commenting/stop`, { method: "POST" });
    setStatus("stopped");
  };

  const checkQueue = async () => {
    const res = await fetch(`${API}/commenting/queue`);
    const data = await res.json();
    setQueueSize(data.queue_size);
  };

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: "24px" }}>Neurocommenting Engine</h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div className="surface-static" style={{ padding: "24px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>Engine Control</div>

          <div style={{ marginBottom: "16px" }}>
            <label className="caption" style={{ display: "block", marginBottom: "8px" }}>Worker Count</label>
            <input type="range" min="1" max="50" value={workers} onChange={e => setWorkers(parseInt(e.target.value))} style={{ width: "100%" }} />
            <span style={{ fontSize: "13px", color: "var(--accent)", fontWeight: 600 }}>{workers} workers</span>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-primary" onClick={startEngine} disabled={status === "running"}>Start Engine</button>
            <button className="btn btn-danger" onClick={stopEngine} disabled={status !== "running"}>Stop Engine</button>
          </div>

          <div style={{ marginTop: "12px", fontSize: "13px" }}>
            Status: <span style={{ color: status === "running" ? "var(--green)" : status === "error" ? "var(--red)" : "var(--text-secondary)", fontWeight: 600 }}>{status}</span>
          </div>
        </div>

        <div className="surface-static" style={{ padding: "24px" }}>
          <div className="section-title" style={{ marginBottom: "16px" }}>Queue Status</div>
          <div style={{ fontSize: "48px", fontWeight: 700, color: "var(--accent)", letterSpacing: "-0.04em" }}>
            {queueSize !== null ? queueSize : "-"}
          </div>
          <div className="caption" style={{ marginBottom: "16px" }}>jobs in queue</div>
          <button className="btn btn-secondary" onClick={checkQueue}>Refresh</button>
        </div>
      </div>
    </div>
  );
}
