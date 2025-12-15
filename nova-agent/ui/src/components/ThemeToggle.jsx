// src/components/ThemeToggle.jsx
import { useEffect, useState } from "react";

function getInitialTheme() {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem("nova-theme");
  if (stored === "light" || stored === "dark") return stored;

  // fallback: system preference
  const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  return prefersDark ? "dark" : "light";
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    const root = document.documentElement;

    root.classList.remove("light", "dark");
    root.classList.add(theme);

    localStorage.setItem("nova-theme", theme);
  }, [theme]);

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      className="theme-switch"
      aria-label="Toggle theme"
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      <div className={`switch-track ${isDark ? "switch-dark" : "switch-light"}`}>
        <div className={`switch-thumb ${isDark ? "thumb-right" : "thumb-left"}`}>
          {isDark ? "🌙" : "☀️"}
        </div>
      </div>
    </button>
  );
}
