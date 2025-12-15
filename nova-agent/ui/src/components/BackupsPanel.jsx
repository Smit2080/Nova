// src/components/BackupsPanel.jsx

export default function BackupsPanel() {
  return (
    <section className="flex flex-col h-full w-full px-4 py-3">
      <header className="mb-3 border-b border-slate-700/50 pb-2 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
            BACKUPS
          </p>
          <p className="text-[0.8rem] text-slate-300/85">
            View and restore previous versions of your project.
          </p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto custom-scroll space-y-3 text-sm text-slate-200">
        <p className="text-slate-300/90">
          This panel will be wired to your backup system in{" "}
          <code className="text-xs bg-slate-900/60 px-1.5 py-0.5 rounded border border-slate-700/70">
            /backups
          </code>{" "}
          and{" "}
          <code className="text-xs bg-slate-900/60 px-1.5 py-0.5 rounded border border-slate-700/70">
            /restore
          </code>{" "}
          endpoints.
        </p>

        <ul className="list-disc ml-5 space-y-1">
          <li>List backups grouped by request_id and timestamp</li>
          <li>Show backup notes like &quot;before merge&quot; / &quot;before tests&quot;</li>
          <li>Allow safe restore into integrated/ with one click</li>
        </ul>

        <p className="text-slate-400/85">
          For now this is just UI space reserved. We will plug in real data
          after backend wiring.
        </p>
      </div>
    </section>
  );
}