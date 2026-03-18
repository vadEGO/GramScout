import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type Theme = "dark" | "light" | "auto";

interface ThemeContextType {
  theme: Theme;
  resolved: "dark" | "light";
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextType>({ theme: "auto", resolved: "light", toggle: () => {} });

function getAutoTheme(): "dark" | "light" {
  const hour = new Date().getHours();
  return (hour >= 7 && hour < 19) ? "light" : "dark";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("gramscout-theme") as Theme) || "auto";
    }
    return "auto";
  });

  const resolved = theme === "auto" ? getAutoTheme() : theme;

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", resolved);
    localStorage.setItem("gramscout-theme", theme);
  }, [resolved, theme]);

  // Re-check auto theme every minute
  useEffect(() => {
    if (theme !== "auto") return;
    const interval = setInterval(() => {
      document.documentElement.setAttribute("data-theme", getAutoTheme());
    }, 60000);
    return () => clearInterval(interval);
  }, [theme]);

  const toggle = () => {
    setTheme(t => t === "light" ? "dark" : t === "dark" ? "auto" : "light");
  };

  return <ThemeContext.Provider value={{ theme, resolved, toggle }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
