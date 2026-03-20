import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { ThemeProvider } from "./ThemeContext";
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
    items: [{ to: "/", label: "Dashboard" }],
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
    items: [{ to: "/settings", label: "Settings" }],
  },
];

const mobileNav = [
  { to: "/", label: "Dashboard" },
  { to: "/analytics", label: "Growth" },
  { to: "/logs", label: "Alerts" },
  { to: "/settings", label: "Settings" },
];

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="app-shell">
          <aside className="sidebar">
            <div className="brand-block">
              <div className="brand-title">GRAMSCOUT</div>
              <div className="brand-subtitle">AI-native Telegram Growth Platform</div>
            </div>

            <nav style={{ flex: 1, padding: "10px 0", overflowY: "auto" }}>
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

            <div className="sidebar-footer">v0.5.0 • Ultra Minimal UI</div>
          </aside>

          <main className="app-main">
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

          <nav className="mobile-nav">
            {mobileNav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) => `mobile-nav-link ${isActive ? "active" : ""}`}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}
