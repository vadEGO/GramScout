import { useEffect, useState } from "react";

const API = "/api/v1";

interface Channel {
  id: string; url: string; name: string; username: string | null;
  subscribers: number; is_target: boolean; open_comments: boolean;
  quality_score: number; topic: string | null;
}

interface Account { id: string; phone: string; status: string; warming_stage: number; persona: any; }

export default function Channels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
  const [targetAccounts, setTargetAccounts] = useState<any[]>([]);

  const load = () => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/channels`).then(r => r.json()),
      fetch(`${API}/accounts`).then(r => r.json()),
    ]).then(([ch, ac]) => { setChannels(ch); setAccounts(ac); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const toggleTarget = async (id: string, current: boolean) => {
    await fetch(`${API}/channels/${id}/target?is_target=${!current}`, { method: "PATCH" });
    load();
  };

  const openAssignment = async (channel: Channel) => {
    setSelectedChannel(channel);
    const res = await fetch(`${API}/accounts/by-channel/${channel.id}`);
    const data = await res.json();
    setTargetAccounts(data);
  };

  const assignAccount = async (accountId: string) => {
    if (!selectedChannel) return;
    await fetch(`${API}/accounts/${accountId}/targets?channel_id=${selectedChannel.id}&priority=5`, { method: "POST" });
    openAssignment(selectedChannel);
  };

  const removeTarget = async (targetId: string) => {
    if (!selectedChannel) return;
    await fetch(`${API}/accounts/placeholder/targets/${targetId}`, { method: "DELETE" });
    openAssignment(selectedChannel);
  };

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: "24px" }}>Channels & Targeting</h1>

      {loading ? (
        <div style={{ textAlign: "center", padding: "48px", color: "var(--text-muted)" }}>Loading...</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Channel</th><th>Subscribers</th><th>Topic</th><th>Quality</th><th>Comments</th><th>Target</th><th>Accounts</th></tr></thead>
            <tbody>
              {channels.map(ch => (
                <tr key={ch.id}>
                  <td><div style={{ fontWeight: 500 }}>{ch.name}</div><div className="caption">@{ch.username || "—"}</div></td>
                  <td style={{ fontVariantNumeric: "tabular-nums" }}>{ch.subscribers.toLocaleString()}</td>
                  <td><span className="caption">{ch.topic || "—"}</span></td>
                  <td style={{ color: ch.quality_score >= 7 ? "var(--green)" : ch.quality_score >= 4 ? "var(--amber)" : "var(--text-muted)" }}>{ch.quality_score.toFixed(1)}</td>
                  <td>{ch.open_comments ? <span className="badge badge-active">Open</span> : <span className="badge badge-muted">Closed</span>}</td>
                  <td>
                    <button onClick={() => toggleTarget(ch.id, ch.is_target)} className={`btn btn-sm ${ch.is_target ? "btn-primary" : "btn-secondary"}`}>
                      {ch.is_target ? "Target" : "Set Target"}
                    </button>
                  </td>
                  <td>
                    <button onClick={() => openAssignment(ch)} className="btn btn-ghost btn-sm">
                      Assign Accounts →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Account Assignment Modal */}
      {selectedChannel && (
        <div className="modal-overlay anim-fade" onClick={() => setSelectedChannel(null)}>
          <div className="modal-content anim-slide" onClick={e => e.stopPropagation()} style={{ maxWidth: "700px" }}>
            <div style={{ padding: "20px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div className="section-title">Assign Accounts to {selectedChannel.name}</div>
                <div className="caption">@{selectedChannel.username}</div>
              </div>
              <button className="btn-icon" onClick={() => setSelectedChannel(null)}>✕</button>
            </div>

            <div style={{ padding: "20px" }}>
              <div style={{ marginBottom: "16px" }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px" }}>Currently Assigned ({targetAccounts.length})</div>
                {targetAccounts.length === 0 ? (
                  <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>No accounts assigned yet</div>
                ) : (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {targetAccounts.map(ta => (
                      <span key={ta.target_id || ta.account_id} className="badge badge-info" style={{ display: "flex", alignItems: "center", gap: "6px", padding: "4px 10px" }}>
                        {ta.phone}
                        <button onClick={() => removeTarget(ta.target_id)} style={{ background: "none", border: "none", color: "var(--red)", cursor: "pointer", fontSize: "14px", lineHeight: 1 }}>×</button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px" }}>Available Accounts</div>
                <div style={{ maxHeight: "300px", overflowY: "auto" }}>
                  {accounts.filter(a => a.status === "active" || a.status === "working").map(acc => (
                    <div key={acc.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", borderBottom: "1px solid var(--border)", cursor: "pointer" }}
                      onClick={() => assignAccount(acc.id)}>
                      <div>
                        <span style={{ fontFamily: "monospace", fontWeight: 500 }}>{acc.phone}</span>
                        <span className="caption" style={{ marginLeft: "8px" }}>{acc.persona?.personality_type || "—"}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <div className="progress-track" style={{ width: "60px" }}>
                          <div className="progress-fill" style={{ width: `${acc.warming_stage}%`, background: acc.warming_stage >= 80 ? "var(--green)" : "var(--amber)" }} />
                        </div>
                        <span className="btn btn-primary btn-sm">+ Assign</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
