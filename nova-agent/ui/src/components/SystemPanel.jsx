// src/components/SystemPanel.jsx

export default function SystemPanel() {
  return (
    <section className="flex flex-col h-full w-full px-4 py-3">
      <header className="mb-3 border-b border-slate-700/50 pb-2 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
            SYSTEM & ENV
          </p>
          <p className="text-[0.8rem] text-slate-300/85">
            Environment info, versions and resource usage (later).
          </p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto custom-scroll space-y-3 text-sm text-slate-200">
        <p className="text-slate-300/90">
          This panel will read metadata from your environment capture:
        </p>

        <ul className="list-disc ml-5 space-y-1">
          <li>Python version, OS, CPU info</li>
          <li>Installed packages (from pip freeze / requirements_pinned)</li>
          <li>Node / npm versions when needed</li>
        </ul>

        <p className="text-slate-400/85">
          Later we can also add:
        </p>
        <ul className="list-disc ml-5 space-y-1">
          <li>Simple CPU / RAM usage summary</li>
          <li>Warnings for risky dependency upgrades</li>
          <li>Buttons to trigger environment scans via the advisor engine</li>
        </ul>
      </div>
    </section>
  );
}