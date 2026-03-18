import { useEffect, useState } from "react";
import { COUNTRIES } from "../data/countries";

const API = "/api/v1";

interface Account {
  id: string;
  phone: string;
  status: string;
  persona: Record<string, any> | null;
  gender: string | null;
  warming_stage: number;
  premium: boolean;
  created_at: string | null;
  last_active: string | null;
}

interface AccountDetail extends Account {
  username: string | null;
  first_name: string | null;
  ban_count: number;
  assigned_model: string | null;
}

const statusBadge: Record<string, string> = {
  active: "badge-active",
  warming: "badge-warning",
  working: "badge-info",
  muted: "badge-muted",
  banned: "badge-danger",
  invalid: "badge-muted",
};

export default function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<AccountDetail | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState({ phone: "", country_code: "+1", session_string: "" });
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<any>({});
  const [countrySearch, setCountrySearch] = useState("");
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);

  const load = () => {
    setLoading(true);
    fetch(`${API}/accounts`).then((r) => r.json()).then(setAccounts).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const addAccount = async () => {
    if (!addForm.phone.trim()) return;
    const params = new URLSearchParams({ phone: addForm.phone, country_code: addForm.country_code });
    await fetch(`${API}/accounts?${params}`, { method: "POST" });
    setAddForm({ phone: "", country_code: "+1", session_string: "" });
    setShowAddForm(false);
    load();
  };

  const openDetail = async (id: string) => {
    const res = await fetch(`${API}/accounts/${id}`);
    const data = await res.json();
    setSelected(data);
    setEditing(false);
    setEditForm({
      first_name: data.first_name || "",
      last_name: data.last_name || "",
      username: data.username || "",
      bio: data.persona?.bio || "",
      gender: data.gender || "unspecified",
      assigned_model: data.assigned_model || "",
      persona_type: data.persona?.personality_type || "",
    });
  };

  const saveEdit = async () => {
    if (!selected) return;
    const params = new URLSearchParams();
    Object.entries(editForm).forEach(([k, v]) => {
      if (v) params.set(k, String(v));
    });
    await fetch(`${API}/accounts/${selected.id}?${params}`, { method: "PUT" });
    setEditing(false);
    openDetail(selected.id);
    load();
  };

  const updateStatus = async (id: string, status: string) => {
    await fetch(`${API}/accounts/${id}/status?status=${status}`, { method: "PATCH" });
    load();
    if (selected?.id === id) openDetail(id);
  };

  const killAccount = async (id: string) => {
    if (!confirm("Kill this account?")) return;
    await fetch(`${API}/killswitch/kill-account?account_id=${id}`, { method: "POST" });
    setSelected(null);
    load();
  };

  const restartAccount = async (id: string) => {
    await fetch(`${API}/killswitch/restart-account?account_id=${id}`, { method: "POST" });
    load();
  };

  const deleteAccount = async (id: string) => {
    await fetch(`${API}/accounts/${id}`, { method: "DELETE" });
    setSelected(null);
    load();
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedIds(next);
  };

  const warmSelected = async () => {
    for (const id of selectedIds) {
      await fetch(`${API}/accounts/${id}/status?status=warming`, { method: "PATCH" });
    }
    setSelectedIds(new Set());
    load();
  };

  const quarantineSelected = async () => {
    const ids = Array.from(selectedIds).join(",");
    await fetch(`${API}/killswitch/quarantine?account_ids=${ids}`, { method: "POST" });
    setSelectedIds(new Set());
    load();
  };

  const filtered = accounts.filter((a) => {
    if (statusFilter !== "all" && a.status !== statusFilter) return false;
    if (search && !a.phone.includes(search)) return false;
    return true;
  });

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Accounts</h1>
          <div className="caption" style={{ marginTop: "4px" }}>{accounts.length} total accounts</div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {selectedIds.size > 0 && (
            <>
              <button className="btn btn-secondary btn-sm" onClick={warmSelected}>Warm Selected ({selectedIds.size})</button>
              <button className="btn btn-secondary btn-sm" onClick={quarantineSelected} style={{ color: "var(--warning)" }}>Quarantine</button>
            </>
          )}
          <button className="btn btn-secondary btn-sm" onClick={() => setShowAddForm(!showAddForm)}>+ Add Account</button>
          <button className="btn btn-secondary btn-sm" onClick={load}>Refresh</button>
        </div>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <div className="card" style={{ marginBottom: "16px" }} >
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "12px" }}>
            <input className="input" placeholder="Phone (+1234567890)" value={addForm.phone}
              onChange={(e) => setAddForm({ ...addForm, phone: e.target.value })} />
            <select className="input" value={addForm.country_code}
              onChange={(e) => setAddForm({ ...addForm, country_code: e.target.value })}>
              <option value="+1">+1 (USA)</option>
              <option value="+44">+44 (UK)</option>
              <option value="+49">+49 (Germany)</option>
              <option value="+380">+380 (Ukraine)</option>
              <option value="+7">+7 (Russia)</option>
            </select>
            <input className="input" type="password" placeholder="Session string (optional)" value={addForm.session_string}
              onChange={(e) => setAddForm({ ...addForm, session_string: e.target.value })} />
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-primary" onClick={addAccount}>Create Account</button>
            <button className="btn btn-ghost" onClick={() => setShowAddForm(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "16px" }}>
        <input className="input" placeholder="Search by phone..." value={search}
          onChange={(e) => setSearch(e.target.value)} style={{ maxWidth: "240px" }} />
        <div style={{ display: "flex", gap: "4px" }}>
          {["all", "active", "warming", "working", "muted", "banned"].map((s) => (
            <button key={s} onClick={() => setStatusFilter(s)}
              className={`btn btn-sm ${statusFilter === s ? "btn-primary" : "btn-ghost"}`}>
              {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div style={{ textAlign: "center", padding: "48px", color: "var(--text-muted)" }}>Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="surface-static" style={{ textAlign: "center", padding: "48px" }}>
          <div style={{ fontSize: "32px", marginBottom: "12px" }}>📭</div>
          <div style={{ color: "var(--text-secondary)" }}>No accounts found</div>
          <button className="btn btn-primary" style={{ marginTop: "16px" }} onClick={() => setShowAddForm(true)}>
            + Add Your First Account
          </button>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ width: "40px" }}>
                  <input type="checkbox" onChange={() => {
                    if (selectedIds.size === filtered.length) setSelectedIds(new Set());
                    else setSelectedIds(new Set(filtered.map(a => a.id)));
                  }} checked={selectedIds.size === filtered.length && filtered.length > 0} />
                </th>
                <th>Phone</th>
                <th>Status</th>
                <th>Gender</th>
                <th>Persona</th>
                <th>Warming</th>
                <th>Premium</th>
                <th style={{ width: "40px" }}></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((acc) => (
                <tr key={acc.id} onClick={() => openDetail(acc.id)} style={{ cursor: "pointer" }}>
                  <td onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={selectedIds.has(acc.id)} onChange={() => toggleSelect(acc.id)} />
                  </td>
                  <td style={{ fontFamily: "monospace", fontWeight: 500 }}>{acc.phone}</td>
                  <td><span className={`badge ${statusBadge[acc.status] || "badge-muted"}`}>{acc.status}</span></td>
                  <td>
                    {acc.gender === "male" ? "👨" : acc.gender === "female" ? "👩" : "—"}
                    <span style={{ marginLeft: "4px", fontSize: "12px", color: "var(--text-secondary)" }}>{acc.gender || "—"}</span>
                  </td>
                  <td style={{ color: "var(--text-secondary)" }}>{acc.persona?.personality_type || "—"}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div className="progress-track" style={{ width: "80px" }}>
                        <div className="progress-fill" style={{
                          width: `${acc.warming_stage}%`,
                          background: acc.warming_stage >= 80 ? "var(--green)" : acc.warming_stage >= 50 ? "var(--amber)" : "var(--accent)",
                        }} />
                      </div>
                      <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>{acc.warming_stage}%</span>
                    </div>
                  </td>
                  <td>{acc.premium ? "⭐" : ""}</td>
                  <td><span style={{ color: "var(--text-muted)" }}>→</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Modal */}
      {selected && (
        <div className="modal-overlay animate-fade" onClick={() => setSelected(null)}>
          <div className="modal-content animate-slide" onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: "24px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: "18px", fontWeight: 600, fontFamily: "monospace" }}>{selected.phone}</div>
                <div className="caption">@{selected.username || "no username"}</div>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button className="btn btn-sm" style={{ color: "var(--danger)" }} onClick={() => deleteAccount(selected.id)}>Delete</button>
                <button className="btn-icon" onClick={() => setSelected(null)}>✕</button>
              </div>
            </div>

            <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
              {/* Status + Edit toggle */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <span className={`badge ${statusBadge[selected.status]}`}>{selected.status}</span>
                  {selected.premium && <span className="badge badge-active">⭐ Premium</span>}
                </div>
                <button className="btn btn-sm btn-secondary" onClick={() => setEditing(!editing)}>
                  {editing ? "Cancel" : "✏️ Edit"}
                </button>
              </div>

              {editing ? (
                /* EDIT MODE */
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                    <div>
                      <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>First Name</label>
                      <input className="input" value={editForm.first_name} onChange={e => setEditForm({ ...editForm, first_name: e.target.value })} />
                    </div>
                    <div>
                      <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>Last Name</label>
                      <input className="input" value={editForm.last_name} onChange={e => setEditForm({ ...editForm, last_name: e.target.value })} />
                    </div>
                    <div>
                      <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>Username</label>
                      <input className="input" value={editForm.username} onChange={e => setEditForm({ ...editForm, username: e.target.value })} />
                    </div>
                    <div>
                      <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>Gender</label>
                      <select className="input" value={editForm.gender} onChange={e => setEditForm({ ...editForm, gender: e.target.value })}>
                        <option value="male">👨 Male</option>
                        <option value="female">👩 Female</option>
                        <option value="unspecified">— Unspecified</option>
                      </select>
                    </div>
                  </div>
            <div>
              <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>Country</label>
              <div style={{ position: "relative" }}>
                <input className="input" placeholder="Search country..." value={countrySearch}
                  onChange={e => { setCountrySearch(e.target.value); setShowCountryDropdown(true); }}
                  onFocus={() => setShowCountryDropdown(true)}
                  onBlur={() => setTimeout(() => setShowCountryDropdown(false), 200)} />
                {showCountryDropdown && (
                  <div style={{ position: "absolute", top: "100%", left: 0, right: 0, maxHeight: "200px", overflowY: "auto", background: "var(--surface-solid)", border: "1px solid var(--border)", borderRadius: "8px", zIndex: 10, boxShadow: "var(--shadow-md)" }}>
                    {COUNTRIES.filter(c =>
                      c.name.toLowerCase().includes(countrySearch.toLowerCase()) ||
                      c.code.includes(countrySearch) ||
                      c.iso.toLowerCase().includes(countrySearch.toLowerCase())
                    ).slice(0, 10).map(c => (
                      <div key={`${c.iso}-${c.code}`}
                        style={{ padding: "8px 12px", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}
                        onMouseDown={() => { setAddForm({ ...addForm, country_code: c.code }); setCountrySearch(`${c.flag} ${c.name} (${c.code})`); setShowCountryDropdown(false); }}>
                        <span>{c.flag}</span>
                        <span>{c.name}</span>
                        <span style={{ color: "var(--text-muted)", marginLeft: "auto" }}>{c.code}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>AI Model</label>
                    <select className="input" value={editForm.assigned_model} onChange={e => setEditForm({ ...editForm, assigned_model: e.target.value })}>
                      <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
                      <option value="openai/gpt-4o">GPT-4o</option>
                      <option value="anthropic/claude-3.5-haiku">Claude 3.5 Haiku</option>
                      <option value="google/gemini-2.0-flash">Gemini 2.0 Flash</option>
                      <option value="deepseek/deepseek-chat-v3">DeepSeek Chat V3</option>
                    </select>
                  </div>
                  <button className="btn btn-primary" onClick={saveEdit}>Save Changes</button>
                </div>
              ) : (
                <>
                  {/* VIEW MODE */}
                  {/* Status buttons */}
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    {["active", "warming", "working", "muted", "banned"].map((s) => (
                      <button key={s} onClick={() => updateStatus(selected.id, s)}
                        className={`btn btn-sm ${selected.status === s ? "btn-primary" : "btn-secondary"}`}>
                        {s}
                      </button>
                    ))}
                  </div>

              {/* Kill / Restart */}
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                <button className="btn btn-sm btn-danger" onClick={() => killAccount(selected.id)}>Kill Account</button>
                {selected.status === "muted" && (
                  <button className="btn btn-sm" style={{ background: "var(--green-light)", color: "var(--green)" }}
                    onClick={() => restartAccount(selected.id)}>Restart</button>
                )}
                <button className="btn btn-sm btn-secondary" onClick={async () => {
                  const res = await fetch(`${API}/accounts/${selected.id}/session`);
                  const data = await res.json();
                  if (data.session_string) {
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                    const a = document.createElement("a");
                    a.href = URL.createObjectURL(blob);
                    a.download = `session_${selected.phone}.json`;
                    a.click();
                  }
                }}>Export Session</button>
              </div>

                  {/* Persona */}
                  {selected.persona && (
                    <div className="surface-static" style={{ padding: "16px" }}>
                      <div className="section-title" style={{ fontSize: "13px", marginBottom: "12px" }}>
                        Persona Profile
                        {selected.gender && (
                          <span style={{ marginLeft: "8px", fontWeight: 400 }}>
                            {selected.gender === "male" ? "👨" : selected.gender === "female" ? "👩" : ""} {selected.gender}
                          </span>
                        )}
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                        {Object.entries(selected.persona).map(([key, value]) => (
                          <div key={key}>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "capitalize" }}>{key.replace(/_/g, " ")}</div>
                            <div style={{ fontSize: "13px", fontWeight: 500 }}>{String(value)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Warming */}
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                      <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>Warming Progress</span>
                      <span style={{ fontSize: "13px", fontWeight: 600 }}>{selected.warming_stage}%</span>
                    </div>
                    <div className="progress-track" style={{ height: "8px" }}>
                      <div className="progress-fill" style={{ width: `${selected.warming_stage}%`, background: "var(--accent)" }} />
                    </div>
                  </div>

                  {/* Stats */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
                    <div className="surface-static" style={{ textAlign: "center", padding: "12px" }}>
                      <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--red)" }}>{selected.ban_count}</div>
                      <div className="caption">Bans</div>
                    </div>
                    <div className="surface-static" style={{ textAlign: "center", padding: "12px" }}>
                      <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--accent)" }}>{selected.warming_stage}</div>
                      <div className="caption">Stage</div>
                    </div>
                    <div className="surface-static" style={{ textAlign: "center", padding: "12px" }}>
                      <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--green)" }}>{selected.assigned_model ? "✓" : "—"}</div>
                      <div className="caption">AI Model</div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
