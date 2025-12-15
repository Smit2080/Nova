// src/components/FilePreview.jsx
import { useEffect } from "react";
import FileIcon, { getFileKind } from "./FileIcon.jsx";

export default function FilePreview({ files, progressById, onRemove }) {
  if (!files || files.length === 0) return null;

  return (
    <div className="px-4 pt-2 pb-2 border-b border-slate-800/70 bg-slate-950/60">
      <p className="text-[0.7rem] uppercase tracking-[0.16em] text-slate-400 mb-1">
        ATTACHED {files.length > 1 ? "FILES" : "FILE"}
      </p>
      <div className="flex flex-wrap gap-2">
        {files.map((item) => {
          const { id, file, previewUrl } = item;
          const kind = getFileKind(file);
          const isImage = kind === "image";
          const progress = progressById?.[id];

          return (
            <div
              key={id}
              className="relative flex items-center gap-2 rounded-xl border border-slate-700/70 bg-slate-900/70 px-2.5 py-2 min-w-[10rem] max-w-xs"
            >
              {/* Thumbnail / Icon */}
              <div className="flex-shrink-0">
                {isImage && previewUrl ? (
                  <div className="w-10 h-10 rounded-md overflow-hidden border border-slate-700/70 bg-slate-950/70">
                    <img
                      src={previewUrl}
                      alt={file.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <FileIcon kind={kind} />
                )}
              </div>

              {/* Name + size */}
              <div className="flex flex-col min-w-0">
                <p className="text-[0.75rem] text-slate-100 truncate max-w-[9rem]">
                  {file.name}
                </p>
                <p className="text-[0.68rem] text-slate-400">
                  {(file.size / 1024).toFixed(1)} KB
                </p>

                {/* Small progress bar (if any) */}
                {typeof progress === "number" && progress < 100 && (
                  <div className="mt-1 h-[3px] rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-cyan-400"
                      style={{ width: `${Math.min(progress, 100)}%` }}
                    />
                  </div>
                )}

                {typeof progress === "number" && progress >= 100 && (
                  <p className="mt-0.5 text-[0.65rem] text-emerald-400">
                    Uploaded
                  </p>
                )}
              </div>

              {/* Remove button */}
              <button
                type="button"
                onClick={() => onRemove(id)}
                className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-slate-900/90 border border-slate-600/80 flex items-center justify-center text-[0.6rem] text-slate-300 hover:text-rose-300 hover:border-rose-400/80"
              >
                ×
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}