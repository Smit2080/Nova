// src/components/FileChip.jsx
export default function FileChip({ file, onRemove }) {
  const getType = (name) => {
    const ext = name.split(".").pop().toLowerCase();
    if (["png", "jpg", "jpeg", "gif", "webp"].includes(ext)) return "img";
    if (ext === "pdf") return "pdf";
    if (["zip", "rar", "7z", "tar"].includes(ext)) return "archive";
    return "file";
  };

  const type = getType(file.name);

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-200 text-xs shrink-0">
      {/* icon */}
      <span
        className={`text-[0.7rem] font-bold ${
          type === "img"
            ? "text-cyan-300"
            : type === "pdf"
            ? "text-red-400"
            : type === "archive"
            ? "text-amber-300"
            : "text-slate-300"
        }`}
      >
        {type === "img" && "IMG"}
        {type === "pdf" && "PDF"}
        {type === "archive" && "ZIP"}
        {type === "file" && "FILE"}
      </span>

      {/* filename */}
      <span className="max-w-[120px] truncate">{file.name}</span>

      {/* remove button */}
      <button
        onClick={onRemove}
        className="text-slate-400 hover:text-red-400 transition text-sm"
      >
        ✕
      </button>
    </div>
  );
}