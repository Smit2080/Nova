// src/components/FileIcon.js

export function getFileKind(file) {
  if (!file) return "file";
  const name = file.name || "";
  const lower = name.toLowerCase();

  if (lower.endsWith(".png") || lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".webp") || lower.endsWith(".gif")) {
    return "image";
  }
  if (lower.endsWith(".pdf")) return "pdf";
  if (lower.endsWith(".zip") || lower.endsWith(".rar") || lower.endsWith(".7z")) return "archive";
  if (lower.endsWith(".doc") || lower.endsWith(".docx")) return "doc";
  if (lower.endsWith(".xls") || lower.endsWith(".xlsx")) return "sheet";
  if (lower.endsWith(".txt") || lower.endsWith(".md")) return "text";
  return "file";
}

export default function FileIcon({ kind }) {
  const base =
    "inline-flex items-center justify-center w-8 h-8 rounded-md text-[0.65rem] font-semibold shrink-0";

  switch (kind) {
    case "image":
      return <div className={`${base} bg-cyan-500/15 border border-cyan-500/50 text-cyan-200`}>IMG</div>;
    case "pdf":
      return <div className={`${base} bg-red-500/15 border border-red-500/50 text-red-300`}>PDF</div>;
    case "archive":
      return <div className={`${base} bg-amber-500/15 border border-amber-500/50 text-amber-200`}>ZIP</div>;
    case "doc":
      return <div className={`${base} bg-blue-500/15 border border-blue-500/50 text-blue-200`}>DOC</div>;
    case "sheet":
      return <div className={`${base} bg-emerald-500/15 border border-emerald-500/50 text-emerald-200`}>XLS</div>;
    case "text":
      return <div className={`${base} bg-slate-500/15 border border-slate-500/50 text-slate-200`}>TXT</div>;
    default:
      return <div className={`${base} bg-slate-500/10 border border-slate-600/70 text-slate-200`}>FILE</div>;
  }
}