// src/App.jsx
import { useState, useMemo } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChatBox from "./components/ChatBox";
import BuilderPanel from "./components/BuilderPanel";
import BackupsPanel from "./components/BackupsPanel";
import SystemPanel from "./components/SystemPanel";
import "./index.css";

// id generator
const makeId = () => Math.random().toString(36).slice(2, 10);

// greeting msg
const makeGreeting = () => ({
  id: Date.now(),
  role: "agent",
  text: "Hi, I’m Nova’s Builder+Agent UI. Tell me what you want to do with your project.",
  files: [],
});

// new chat object
const makeConversation = () => ({
  id: makeId(),
  title: "New chat",
  messages: [makeGreeting()],
});

export default function App() {
  const [conversations, setConversations] = useState(() => [makeConversation()]);
  const [activeId, setActiveId] = useState(conversations[0].id);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [statusOpen, setStatusOpen] = useState(false);

  // Which main panel is active
  const [activePanelId, setActivePanelId] = useState("chat");

  const handleToggleSidebar = () => setSidebarOpen((v) => !v);
  const handleToggleStatus = () => setStatusOpen((v) => !v);

  const closeAll = () => {
    setSidebarOpen(false);
    setStatusOpen(false);
  };

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) || conversations[0],
    [conversations, activeId]
  );

  // NEW CHAT
  const handleNewChat = () => {
    const conv = makeConversation();
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
    setActivePanelId("chat");
  };

  // SELECT chat
  const handleSelectConversation = (id) => {
    setActiveId(id);
    setActivePanelId("chat");
  };

  // BACKEND-CONNECTED MESSAGE HANDLER
  const handleSendMessage = async ({ text }) => {
    if (!text.trim()) return;

    // add user message instantly
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeConversation.id
          ? {
              ...conv,
              messages: [
                ...conv.messages,
                {
                  id: Date.now(),
                  role: "user",
                  text,
                  files: [],
                },
              ],
            }
          : conv
      )
    );

    try {
      const res = await fetch("http://127.0.0.1:9001/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          role: "user",
          session_id: activeConversation.id,
          request_id: null,   //  🔥 REQUIRED FIX
        }),
      });

      const data = await res.json();

      // add agent reply
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === activeConversation.id
            ? {
                ...conv,
                messages: [
                  ...conv.messages,
                  {
                    id: Date.now() + 1,
                    role: "agent",
                    text: data.reply,
                    files: [],
                  },
                ],
              }
            : conv
        )
      );
    } catch (err) {
      console.error(err);

      // fallback error message
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === activeConversation.id
            ? {
                ...conv,
                messages: [
                  ...conv.messages,
                  {
                    id: Date.now() + 1,
                    role: "agent",
                    text: "Error: Cannot reach server.",
                    files: [],
                  },
                ],
              }
            : conv
        )
      );
    }
  };

  // Which center panel to render
  const renderCenterPanel = () => {
    switch (activePanelId) {
      case "builder":
        return <BuilderPanel />;
      case "backups":
        return <BackupsPanel />;
      case "system":
        return <SystemPanel />;
      case "chat":
      default:
        return (
          <ChatBox
            messages={activeConversation.messages}
            onSend={handleSendMessage}
            onOpenOutput={handleToggleStatus}
          />
        );
    }
  };

  return (
    <div className="h-screen neon-bg flex flex-col overflow-hidden">
      {/* HEADER */}
      <div className="w-full px-4 py-3 md:px-6 lg:px-10 shrink-0">
        <Header
          onToggleSidebar={handleToggleSidebar}
          onToggleOutput={handleToggleStatus}
        />
      </div>

      {/* MAIN layout */}
      <div className="flex-1 flex min-h-0 px-4 pb-4 md:px-6 lg:px-10 gap-4">
        {/* LEFT sidebar */}
        <div className="hidden lg:block w-64 shrink-0">
          <div className="glass-card h-full rounded-3xl p-3">
            <Sidebar
              conversations={conversations}
              activeConversationId={activeConversation.id}
              activePanelId={activePanelId}
              onNewChat={handleNewChat}
              onSelectConversation={handleSelectConversation}
              onChangePanel={setActivePanelId}
            />
          </div>
        </div>

        {/* CENTER PANEL */}
        <div className="flex-1 flex min-h-0">
          <div className="glass-card rounded-3xl flex flex-col w-full overflow-hidden h-full">
            {renderCenterPanel()}
          </div>
        </div>
      </div>

      {/* MOBILE sidebar */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
            onClick={closeAll}
          />
          <div className="fixed inset-y-0 left-0 w-64 z-50 p-3 lg:hidden">
            <div className="glass-card h-full rounded-3xl p-3 flex flex-col">
              <Sidebar
                conversations={conversations}
                activeConversationId={activeConversation.id}
                activePanelId={activePanelId}
                onNewChat={() => {
                  handleNewChat();
                  closeAll();
                }}
                onSelectConversation={(id) => {
                  handleSelectConversation(id);
                  closeAll();
                }}
                onChangePanel={(panelId) => {
                  setActivePanelId(panelId);
                  closeAll();
                }}
              />
            </div>
          </div>
        </>
      )}

      {/* RIGHT OUTPUT PANEL */}
      {statusOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px]"
            onClick={closeAll}
          />

          <div className="fixed inset-y-0 right-0 w-full max-w-sm z-50 p-4">
            <div className="glass-card h-full rounded-3xl p-4 flex flex-col text-sm text-slate-200">

              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
                    Output / Status
                  </p>
                  <p className="text-[0.8rem] text-slate-300/90">
                    Builder output will appear here.
                  </p>
                </div>

                <button
                  onClick={closeAll}
                  className="px-2 py-1 rounded-lg bg-slate-900/70 border border-slate-700/70"
                >
                  ✕
                </button>
              </div>

              <ul className="list-disc ml-4 text-sm text-slate-300 space-y-1">
                <li>UI previews</li>
                <li>Code diffs</li>
                <li>Build / test logs</li>
                <li>Uploaded files</li>
                <li>Vision / OCR results</li>
              </ul>

            </div>
          </div>
        </>
      )}
    </div>
  );
}