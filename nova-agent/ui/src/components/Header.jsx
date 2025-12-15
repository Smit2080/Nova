// src/components/Header.jsx
import ThemeToggle from "./ThemeToggle";

export default function Header({ onToggleSidebar, onToggleOutput }) {
  return (
    <header className="flex items-center justify-between gap-4">

      {/* LEFT SIDE */}
      <div className="flex items-center gap-3">

        <button
          type="button"
          onClick={onToggleSidebar}
          className="inline-flex lg:hidden items-center justify-center h-9 w-9 rounded-xl bg-slate-900/70 border border-slate-700/70 text-slate-100 hover:bg-slate-800/80"
        >
          ☰
        </button>

        <div className="relative">
          <div className="h-9 w-9 rounded-2xl bg-gradient-to-br from-cyan-400 via-sky-500 to-fuchsia-500 shadow-[0_0_25px_rgba(56,189,248,0.7)]" />
          <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-slate-950/90">
            N
          </div>
        </div>

        <div>
          <h1 className="neon-text text-xl sm:text-2xl font-semibold tracking-wide">
            Nova Builder + Agent
          </h1>
          <p className="text-xs sm:text-sm text-slate-300/80">
            Local dev assistant · sandbox, backups, and smart suggestions.
          </p>
        </div>
      </div>

      {/* RIGHT SIDE */}
      <div className="flex items-center gap-4">

        {/* Only 1 button — clean */}
        <button
          type="button"
          onClick={onToggleOutput}
          className="flex items-center gap-2 text-xs sm:text-sm px-3 py-1.5 rounded-full bg-slate-900/60 border border-slate-700/70 text-slate-200 hover:bg-slate-800/80"
        >
          View output
        </button>

        <ThemeToggle />
      </div>
    </header>
  );
}