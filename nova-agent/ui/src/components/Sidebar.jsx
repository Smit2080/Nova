// src/components/Sidebar.jsx

const panelItems = [
  { id: "chat", label: "Chat", hotkey: "C" },
  { id: "builder", label: "Builder Runs", hotkey: "B" },
  { id: "backups", label: "Backups", hotkey: "K" },
  { id: "system", label: "System & Env", hotkey: "S" },
];

export default function Sidebar({
  conversations,
  activeConversationId,
  activePanelId,
  onNewChat,
  onSelectConversation,
  onChangePanel,
}) {
  return (
    <aside className="sidebar glass-subpanel flex flex-col gap-3 p-3 rounded-2xl h-full">
      {/* NEW CHAT BUTTON */}
      <button
        type="button"
        onClick={onNewChat}
        className="w-full mb-1 inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-cyan-400/90 to-sky-500/90 text-slate-950 text-sm font-semibold py-2 shadow-[0_0_20px_rgba(56,189,248,0.7)] hover:brightness-110 active:scale-95 transition"
      >
        + New chat
      </button>

      {/* PANEL SECTION */}
      <p className="text-xs uppercase tracking-[0.18em] text-slate-400/85 mb-1">
        PANEL
      </p>

      <nav className="flex flex-col gap-1.5 text-sm">
        {panelItems.map((item) => {
          const active = item.id === activePanelId;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onChangePanel && onChangePanel(item.id)}
              className={`sidebar-item group ${
                active ? "sidebar-item-active" : ""
              }`}
            >
              <span>{item.label}</span>
              <span className="text-[0.7rem] px-1.5 py-0.5 rounded-md border border-slate-500/50 bg-slate-900/40 group-hover:bg-slate-800/70">
                {item.hotkey}
              </span>
            </button>
          );
        })}
      </nav>

      {/* CHAT HISTORY SECTION */}
      <div className="mt-4 pt-3 border-t border-slate-700/50">
        <div className="flex items-center justify-between mb-1.5">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-400/85">
            Chats
          </p>
          <span className="text-[0.65rem] text-slate-500">
            {conversations.length}
          </span>
        </div>

        <div className="space-y-1.5 max-h-64 overflow-y-auto custom-scroll pr-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              type="button"
              onClick={() => onSelectConversation(conv.id)}
              className={`w-full text-left text-xs px-2.5 py-1.5 rounded-lg border ${
                conv.id === activeConversationId
                  ? "bg-cyan-500/15 border-cyan-400/70 text-slate-50 shadow-[0_0_16px_rgba(34,211,238,0.7)]"
                  : "bg-slate-900/40 border-slate-700/60 text-slate-300/90 hover:bg-slate-800/80"
              }`}
            >
              <span className="block truncate">
                {conv.title || "New chat"}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* CURRENT MODE FOOTER */}
      <div className="mt-auto pt-3 border-t border-slate-700/50 text-xs text-slate-400/85">
        <p className="font-medium mb-1 text-slate-300">Current mode</p>
        <p>• Manual control</p>
        <p>• Local sandbox only</p>
      </div>
    </aside>
  );
}