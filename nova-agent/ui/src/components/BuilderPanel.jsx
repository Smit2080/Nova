// src/components/BuilderPanel.jsx

export default function BuilderPanel() {
  return (
    <section className="flex flex-col h-full w-full px-4 py-3">
      <header className="mb-3 border-b border-slate-700/50 pb-2 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
            BUILDER PIPELINE
          </p>
          <p className="text-[0.8rem] text-slate-300/85">
            Plan → prepare workspace → apply patch → run tests → merge.
          </p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto custom-scroll space-y-3 text-sm text-slate-200">
        <p className="text-slate-300/90">
          This is a placeholder for the automated Builder+Agent pipeline UI.
          We will wire it to your FastAPI endpoints:
        </p>

        <ul className="list-disc ml-5 space-y-1">
          <li>/plan – analyse code and create a change plan</li>
          <li>/prepare – create workspace & backups</li>
          <li>/apply_patch – write patches into sandbox</li>
          <li>/run_tests – run Python tests / checks</li>
          <li>/merge – copy from sandbox into integrated/</li>
          <li>/rollback – restore from backup if something breaks</li>
        </ul>

        <p className="text-slate-400/90">
          Later we will:
        </p>
        <ul className="list-disc ml-5 space-y-1">
          <li>Show step-by-step logs for each pipeline run</li>
          <li>Allow you to approve/reject patches</li>
          <li>Display code diffs and errors in a readable way</li>
        </ul>
      </div>
    </section>
  );
}