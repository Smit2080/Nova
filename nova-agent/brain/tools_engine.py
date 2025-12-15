# brain/tools_engine.py

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Callable

BASE = Path(__file__).resolve().parent.parent  # repo root
INTEGRATED_ROOT = BASE / "integrated"
WORKSPACE_ROOT = BASE / "workspace"


# ---------- helpers ----------

def _normalize_root(root: str) -> Path:
    """
    Map a logical root name to a real folder.
    Allowed: 'integrated', 'workspace', 'base'.
    """
    r = (root or "integrated").lower()
    if r == "integrated":
        return INTEGRATED_ROOT
    if r == "workspace":
        return WORKSPACE_ROOT
    if r == "base":
        return BASE
    # default safest = integrated
    return INTEGRATED_ROOT


def _safe_join(root: Path, rel_path: str) -> Path:
    """
    Prevent tools from escaping the project folder.
    Only allow paths inside the chosen root.
    """
    if not rel_path:
        raise ValueError("path is required")

    rel_path = rel_path.replace("\\", "/").lstrip("/")  # force relative
    full = (root / rel_path).resolve()

    if not str(full).startswith(str(root.resolve())):
        raise ValueError("path escapes allowed root")

    return full


# ---------- tool definitions ----------

@dataclass
class ToolSpec:
    name: str
    description: str
    dangerous: bool   # if True => requires explicit user confirmation
    func: Callable[[Dict[str, Any]], Dict[str, Any]]


# ---- Filesystem tools ----

def tool_read_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    args: { "path": "relative/path", "root": "integrated|workspace|base" }
    """
    root = _normalize_root(args.get("root", "integrated"))
    path = _safe_join(root, args.get("path", ""))

    if not path.exists():
        return {"ok": False, "error": f"file not found: {path}"}

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return {
            "ok": True,
            "path": str(path),
            "size": path.stat().st_size,
            "content": text,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(path)}


def tool_write_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    SAFE MODE: this is *dangerous* => must be confirmed by user first.

    args: {
      "path": "relative/path",
      "content": "full file content",
      "root": "integrated|workspace|base",
      "overwrite": true|false
    }
    """
    root = _normalize_root(args.get("root", "integrated"))
    path = _safe_join(root, args.get("path", ""))
    overwrite = bool(args.get("overwrite", True))

    if path.exists() and not overwrite:
        return {"ok": False, "error": f"file already exists: {path}"}

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args.get("content", ""), encoding="utf-8")
        return {"ok": True, "path": str(path), "bytes_written": len(args.get("content", ""))}
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(path)}


def tool_delete_path(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dangerous: delete file or folder.

    args: { "path": "relative/path", "root": "integrated|workspace|base" }
    """
    root = _normalize_root(args.get("root", "integrated"))
    path = _safe_join(root, args.get("path", ""))

    try:
        if path.is_dir():
            # only delete non-root and non-empty is allowed here
            for child in path.rglob("*"):
                if child.is_file():
                    child.unlink()
            path.rmdir()
            kind = "dir"
        elif path.is_file():
            path.unlink()
            kind = "file"
        else:
            return {"ok": False, "error": f"path not found: {path}"}

        return {"ok": True, "path": str(path), "kind": kind}
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(path)}


def tool_list_dir(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    args: { "path": "relative/path" (optional), "root": "integrated|workspace|base" }
    """
    root = _normalize_root(args.get("root", "integrated"))
    rel = args.get("path", "") or "."
    path = _safe_join(root, rel)

    if not path.exists():
        return {"ok": False, "error": f"path not found: {path}"}

    try:
        entries = []
        for c in path.iterdir():
            entries.append({
                "name": c.name,
                "is_dir": c.is_dir(),
                "size": c.stat().st_size if c.is_file() else None,
            })
        return {"ok": True, "path": str(path), "entries": entries}
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(path)}


# ---- Process / command tools ----

def tool_run_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dangerous: can execute arbitrary commands (SAFE MODE => must confirm).

    args: {
      "cmd": "string or list",
      "cwd_root": "integrated|workspace|base",
      "timeout": seconds (optional, default 60)
    }
    """
    cmd = args.get("cmd")
    if not cmd:
        return {"ok": False, "error": "cmd is required"}

    if isinstance(cmd, str):
        shell = True
    elif isinstance(cmd, list):
        shell = False
    else:
        return {"ok": False, "error": "cmd must be string or list"}

    cwd_root = _normalize_root(args.get("cwd_root", "integrated"))
    timeout = int(args.get("timeout", 60))

    try:
        proc = subprocess.run(
            cmd,
            shell=shell,
            cwd=str(cwd_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_run_python_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    args: {
      "path": "relative/path/to/script.py",
      "root": "integrated|workspace|base",
      "timeout": seconds (default 60)
    }
    """
    root = _normalize_root(args.get("root", "integrated"))
    path = _safe_join(root, args.get("path", ""))
    timeout = int(args.get("timeout", 60))

    if not path.exists():
        return {"ok": False, "error": f"script not found: {path}"}

    try:
        proc = subprocess.run(
            ["python", str(path)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------- registry + public API ----------

TOOLS: Dict[str, ToolSpec] = {
    "read_file": ToolSpec(
        name="read_file",
        description="Read a text file from the project (integrated/workspace).",
        dangerous=False,
        func=tool_read_file,
    ),
    "list_dir": ToolSpec(
        name="list_dir",
        description="List files and folders inside a directory.",
        dangerous=False,
        func=tool_list_dir,
    ),
    "write_file": ToolSpec(
        name="write_file",
        description="Create or overwrite a file with new content.",
        dangerous=True,
        func=tool_write_file,
    ),
    "delete_path": ToolSpec(
        name="delete_path",
        description="Delete a file or directory (careful).",
        dangerous=True,
        func=tool_delete_path,
    ),
    "run_command": ToolSpec(
        name="run_command",
        description="Run a shell/terminal command in the project root.",
        dangerous=True,
        func=tool_run_command,
    ),
    "run_python_file": ToolSpec(
        name="run_python_file",
        description="Execute a Python script file in the project.",
        dangerous=True,
        func=tool_run_python_file,
    ),
}


def list_tools() -> Dict[str, Any]:
    """Return metadata about all tools; used by UI or LLM."""
    out = []
    for name, spec in TOOLS.items():
        out.append({
            "name": spec.name,
            "description": spec.description,
            "dangerous": spec.dangerous,
        })
    return {"tools": out}


def run_tool(tool_name: str, args: Dict[str, Any], confirm: bool = False) -> Dict[str, Any]:
    """
    Safe-mode executor.

    - If tool is dangerous AND confirm=False -> do NOT run, just ask for confirmation.
    - Otherwise, execute and return result.
    """
    if tool_name not in TOOLS:
        return {"ok": False, "error": f"unknown tool: {tool_name}"}

    spec = TOOLS[tool_name]

    if spec.dangerous and not confirm:
        # tell the caller to ask human
        return {
            "ok": False,
            "needs_confirmation": True,
            "tool": tool_name,
            "args": args,
            "message": f"Tool '{tool_name}' can modify files or run commands. Ask the user for approval.",
        }

    # run underlying function
    try:
        result = spec.func(args or {})
        # always echo which tool ran
        result.setdefault("tool", tool_name)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": tool_name}