// src/components/ChatBox.jsx
import { useEffect, useRef, useState } from "react";

export default function ChatBox({ messages, onSend, onOpenOutput }) {
  const [input, setInput] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  const fileInputRef = useRef(null);
  const bottomRef = useRef(null);
  const listRef = useRef(null);

  // auto-scroll on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // detect scroll position
  const handleScroll = () => {
    const el = listRef.current;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    setShowScrollBtn(!atBottom);
  };

  const formatSize = (b) => {
    if (!b && b !== 0) return "";
    const kb = b / 1024;
    return kb < 1024 ? kb.toFixed(1) + " KB" : (kb / 1024).toFixed(1) + " MB";
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed && selectedFiles.length === 0) return;

    onSend?.({ text: trimmed, files: selectedFiles });

    setInput("");
    setSelectedFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const getExtension = (n) => (n?.split(".").pop() || "").toLowerCase();

  return (
    <section className="flex flex-col h-full w-full">

      {/* HEADER */}
      <div className="px-4 py-3 border-b border-slate-700/40 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-400">CONSOLE</p>
          <p className="text-[0.78rem] text-slate-300/85">
            Talk to Nova like ChatGPT. Attach files and ask anything.
          </p>
        </div>

        
      </div>

      {/* MESSAGES LIST */}
      <div
        ref={listRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-3 space-y-3 custom-scroll relative"
      >
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={msg.role === "user" ? "chat-bubble chat-bubble-user" : "chat-bubble chat-bubble-agent"}>
              {msg.text && <p className="text-[0.8rem] whitespace-pre-wrap mb-1.5">{msg.text}</p>}

              {Array.isArray(msg.files) && msg.files.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {msg.files.map((f, i) => (
                    <div key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-slate-900/60 border border-slate-700/70 text-[0.7rem]">
                      <span className="w-5 h-5 rounded bg-slate-800/70 flex items-center justify-center text-[0.65rem]">
                        {getExtension(f.name).slice(0, 3).toUpperCase()}
                      </span>
                      <span className="max-w-[150px] truncate">{f.name}</span>
                      <span className="text-slate-400/80">· {formatSize(f.size)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      {/* FLOATING SCROLL BUTTON (ChatGPT style, centered) */}
{showScrollBtn && (
  <button
    onClick={() => bottomRef.current?.scrollIntoView({ behavior: "smooth" })}
    className="
      fixed
      bottom-24
      left-1/2
      -translate-x-1/2
      z-40
      w-10
      h-10
      rounded-full
      bg-slate-800/80
      border border-slate-700
      shadow-[0_0_12px_rgba(0,0,0,0.35)]
      backdrop-blur-md
      flex items-center justify-center
      text-xl text-slate-300
      hover:bg-slate-700/80
      active:scale-95
      transition
    "
  >
    ⬇️
  </button>
)}

      {/* INPUT SECTION */}
      <form onSubmit={handleSubmit} className="border-t border-slate-700/50 px-4 py-3 bg-slate-950/40 flex items-center gap-3">

        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="inline-flex items-center justify-center w-9 h-9 rounded-xl bg-slate-900/70 border border-slate-700/70 text-slate-300 text-lg"
        >
          +
        </button>

        <input
          className="flex-1 bg-slate-900/60 border border-slate-700/60 rounded-xl px-3 py-2 text-sm outline-none"
          placeholder="Type naturally…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />

        <button type="submit" className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-semibold">
          Send
        </button>
      </form>
    </section>
  );
}