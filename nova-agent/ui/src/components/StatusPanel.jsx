// src/components/StatusPanel.jsx
export default function StatusPanel({ open, onClose }) {
  if (!open) return null;

  return (
    <>
      {/* backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* panel */}
      <div className="fixed top-[5rem] right-3 sm:right-6 z-50 w-full max-w-sm">
        <div className="glass-card rounded-3xl p-4 sm:p-5 text-xs sm:text-[0.8rem]">
          {/* header row */}
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-[0.7rem] uppercase tracking-[0.18em] text-slate-400">
                nova core
              </p>
              <p className="neon-text font-semibold text-sm">Status overview</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-slate-300/80 text-xs px-2 py-1 rounded-full bg-slate-900/60 border border-slate-700/70 hover:bg-slate-800/70 active:scale-95 transition"
            >
              Close
            </button>
          </div>

          {/* core bubble */}
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-cyan-400 via-sky-500 to-fuchsia-500 shadow-[0_0_20px_rgba(56,189,248,0.8)] flex items-center justify-center text-[0.7rem] font-semibold text-slate-950/90">
              v0
            </div>
            <div>
              <p className="text-[0.8rem] font-medium text-slate-100">
                Nova Core · Stable
              </p>
              <p className="text-[0.72rem] text-slate-400">
                Builder backend: <span className="text-emerald-400">running</span>
              </p>
            </div>
          </div>

          {/* env snapshot */}
          <div className="border border-slate-700/60 rounded-2xl p-3 bg-slate-950/40 mb-3">
            <p className="text-[0.72rem] text-slate-400 mb-1.5">
              Environment snapshot
            </p>
            <ul className="text-[0.72rem] text-slate-200 space-y-1">
              <li>• Versions pinned from last capture</li>
              <li>• Backups available per request_id</li>
              <li>• Internet access: permission-gated</li>
            </ul>
          </div>

          {/* quick tips */}
          <div className="border border-cyan-500/40 rounded-2xl p-3 bg-cyan-500/5">
            <p className="text-[0.72rem] text-cyan-200 mb-1">
              Quick tips
            </p>
            <ul className="text-[0.72rem] text-slate-100 space-y-1">
              <li>• Ask: “nova, check env and suggest what we should improve first…”</li>
              <li>• Use Backups panel before risky merges.</li>
              <li>• Enable internet only when you actually need fresh info.</li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}
