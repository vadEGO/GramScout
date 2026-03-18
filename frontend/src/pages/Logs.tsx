import { useState } from "react";

const API = "/api/v1";

export default function Logs() {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [hours, setHours] = useState(24);
  const [actionFilter, setActionFilter] = useState("all");

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <h1 className="page-title">Activity Logs</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", cursor: "pointer" }}>
            <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
            <span style={{ color: autoRefresh ? "var(--green)" : "var(--text-muted)" }}>Auto-refresh {autoRefresh ? "ON" : "OFF"}</span>
          </label>
          <div style={{ display: "flex", gap: "4px" }}>
            {[1, 6, 12, 24, 48].map(h => (
              <button key={h} onClick={() => setHours(h)} className={`btn btn-sm ${hours === h ? "btn-primary" : "btn-ghost"}`}>{h}h</button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "4px", marginBottom: "16px" }}>
        {["all", "subscribe", "comment", "react", "read", "view_profile"].map(action => (
          <button key={action} onClick={() => setActionFilter(action)} className={`btn btn-sm ${actionFilter === action ? "btn-primary" : "btn-ghost"}`}>
            {action === "all" ? "All" : action}
          </button>
        ))}
      </div>

      <div className="surface-static" style={{ padding: "24px", textAlign: "center" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "13px" }}>
          Action history will appear here once agents start performing actions.
        </div>
        <div style={{ marginTop: "12px", display: "flex", justifyContent: "center", gap: "16px", fontSize: "12px", color: "var(--text-muted)" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--green)", display: "inline-block" }}></span> Success</span>
          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--red)", display: "inline-block" }}></span> Failed</span>
          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--amber)", display: "inline-block" }}></span> Muted</span>
          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--red)", display: "inline-block" }}></span> Banned</span>
        </div>
      </div>
    </div>
  );
}
