import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { ThemeProvider, useTheme } from "./ThemeContext";
import Dashboard from "./pages/Dashboard";
import Accounts from "./pages/Accounts";
import Channels from "./pages/Channels";
import Commenting from "./pages/Commenting";
import Analytics from "./pages/Analytics";
import Proxies from "./pages/Proxies";
import Warming from "./pages/Warming";
import Reactions from "./pages/Reactions";
import Settings from "./pages/Settings";
import Logs from "./pages/Logs";
import Prompts from "./pages/Personalities";
import ChannelParser from "./pages/ChannelParser";
import Agent from "./pages/Agent";
import Revenue from "./pages/Revenue";

const navSections = [
  {
    label: "Overview",
    items: [
      { to: "/", label: "Dashboard" },
    ],
  },
  {
    label: "Agent",
    items: [
      { to: "/agent", label: "Agent Control" },
      { to: "/revenue", label: "Revenue" },
    ],
  },
  {
    label: "Assets",
    items: [
      { to: "/accounts", label: "Accounts" },
      { to: "/proxies", label: "Proxies" },
      { to: "/channels", label: "Channels" },
    ],
  },
  {
    label: "Engines",
    items: [
      { to: "/commenting", label: "Commenting" },
      { to: "/reactions", label: "Reactions" },
      { to: "/warming", label: "Warming" },
    ],
  },
  {
    label: "Tools",
    items: [
      { to: "/parser", label: "Parser" },
              { to: "/prompts", label: "Personalities" },
      { to: "/logs", label: "Logs" },
      { to: "/analytics", label: "Analytics" },
    ],
  },
  {
    label: "System",
    items: [
      { to: "/settings", label: "Settings" },
    ],
  },
];

export default function App() {
  return (
    <ThemeProvider>
      <AppInner />
    </ThemeProvider>
  );
}

function AppInner() {
  const { theme, toggle } = useTheme();

  return (
    <BrowserRouter>
      <div style={{ display: "flex", height: "100vh", background: "var(--bg)" }}>
        <aside className="sidebar">
          <div style={{ padding: "20px 16px", borderBottom: "1px solid var(--border)" }}>
            <div style={{ fontSize: "18px", fontWeight: 700, color: "var(--text)", letterSpacing: "-0.02em" }}>
              GramScout
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
              Telegram Growth Platform
            </div>
          </div>

          <nav style={{ flex: 1, padding: "8px 0", overflowY: "auto" }}>
            {navSections.map((section) => (
              <div key={section.label}>
                <div className="sidebar-section">{section.label}</div>
                {section.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>

          {/* Theme Toggle */}
          <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)" }}>
            <button
              onClick={toggle}
              className="btn btn-secondary btn-sm"
              style={{ width: "100%", justifyContent: "center", fontSize: "12px" }}
            >
              {theme === "light" ? "☀️ Light" : theme === "dark" ? "🌙 Dark" : "🔄 Auto"}
            </button>
          </div>

          <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", fontSize: "11px", color: "var(--text-muted)" }}>
            v0.4.0
          </div>
        </aside>

        <main style={{ flex: 1, overflow: "auto", padding: "32px 40px" }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agent" element={<Agent />} />
            <Route path="/revenue" element={<Revenue />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/proxies" element={<Proxies />} />
            <Route path="/channels" element={<Channels />} />
            <Route path="/commenting" element={<Commenting />} />
            <Route path="/reactions" element={<Reactions />} />
            <Route path="/warming" element={<Warming />} />
            <Route path="/parser" element={<ChannelParser />} />
            <Route path="/prompts" element={<Prompts />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
