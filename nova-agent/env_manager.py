# env_manager.py
import subprocess
import sys
import json
import platform
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

BASE = Path(__file__).resolve().parent

def _run_cmd(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if out.returncode == 0:
            return out.stdout.strip()
        return None
    except Exception:
        return None

def pip_freeze(python_executable: str = "python"):
    """
    Return pip freeze lines and a name->version dict.
    Uses the provided python executable (so it runs inside venv if needed).
    """
    out = _run_cmd([python_executable, "-m", "pip", "freeze"])
    if not out:
        return {"lines": [], "packages": {}}
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    pkgs = {}
    for line in lines:
        if "==" in line:
            name, ver = line.split("==", 1)
            pkgs[name] = ver
        else:
            pkgs[line] = None
    return {"lines": lines, "packages": pkgs}

def node_info():
    """
    Detect node and npm versions if available.
    """
    node_v = _run_cmd(["node", "-v"])
    npm_v = _run_cmd(["npm", "-v"])
    npm_list = None
    if shutil.which("npm"):
        try:
            out = subprocess.run(["npm", "ls", "--json", "--depth=0"], capture_output=True, text=True, timeout=30)
            if out.returncode == 0 and out.stdout:
                npm_json = json.loads(out.stdout)
                deps = npm_json.get("dependencies", {}) or {}
                npm_list = {k: v.get("version") for k, v in deps.items()}
        except Exception:
            npm_list = None
    return {"node_version": node_v, "npm_version": npm_v, "npm_top_level": npm_list}

def capture_environment(request_id: str, dest_dir: Optional[str | Path] = None) -> Dict[str, Any]:
    """
    Capture environment metadata and optionally write JSON into dest_dir.
    Returns the metadata dict.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    python_exe = sys.executable  # the python binary running the server (venv if active)
    py_version = platform.python_version()
    os_info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

    pip = pip_freeze(python_executable=python_exe)
    node = node_info()

    meta = {
        "request_id": request_id,
        "captured_at": timestamp,
        "python_executable": python_exe,
        "python_version": py_version,
        "os": os_info,
        "pip_freeze_lines": pip["lines"],
        "pip_packages": pip["packages"],
        "node_info": node
    }

    if dest_dir:
        d = Path(dest_dir)
        d.mkdir(parents=True, exist_ok=True)
        outp = d / f"environment_{request_id}.meta.json"
        with open(outp, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        meta["saved_path"] = str(outp)

    return meta
