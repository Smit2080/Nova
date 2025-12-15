# backup_manager.py
import os
import zipfile
import json
import uuid
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
BACKUP_ROOT = BASE / "backups"
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

def _sha256_of_file(path: Path, block_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()

def create_backup(request_id: str, targets: list, repo_root: str | Path = None, note: str = "") -> dict:
    repo_root = Path(repo_root) if repo_root else BASE
    repo_root = repo_root.expanduser().resolve()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
    backup_dir = _ensure_dir(BACKUP_ROOT / request_id)
    zip_path = backup_dir / f"backup_{backup_id}.zip"
    meta_path = backup_dir / f"backup_{backup_id}.json"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if not targets:
            for root, _, files in os.walk(repo_root):
                for f in files:
                    full = Path(root) / f
                    arc = full.relative_to(repo_root)
                    zf.write(full, arcname=str(arc))
        else:
            for t in targets:
                tpath = (repo_root / t).resolve()
                if not tpath.exists():
                    continue
                if tpath.is_file():
                    zf.write(tpath, arcname=str(tpath.relative_to(repo_root)))
                else:
                    for root, _, files in os.walk(tpath):
                        for f in files:
                            full = Path(root) / f
                            arc = full.relative_to(repo_root)
                            zf.write(full, arcname=str(arc))

    # compute checksum
    checksum = _sha256_of_file(zip_path)

    metadata = {
        "backup_id": backup_id,
        "request_id": request_id,
        "timestamp": timestamp,
        "zip_path": str(zip_path),
        "zip_sha256": checksum,
        "repo_root": str(repo_root),
        "targets": targets,
        "note": note
    }
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump(metadata, mf, indent=2)
    return metadata

def list_backups(request_id: str = None) -> list:
    out = []
    if request_id:
        d = BACKUP_ROOT / request_id
        if not d.exists():
            return []
        for f in sorted(d.glob("backup_*.json"), reverse=True):
            try:
                out.append(json.load(open(f, "r", encoding="utf-8")))
            except:
                pass
    else:
        for f in sorted(BACKUP_ROOT.rglob("backup_*.json"), reverse=True):
            try:
                out.append(json.load(open(f, "r", encoding="utf-8")))
            except:
                pass
    return out

def restore_backup(backup_meta: dict, restore_to: str | Path = None) -> dict:
    zip_path = Path(backup_meta["zip_path"])
    if not zip_path.exists():
        return {"status": "error", "error": "zip_missing"}
    target_root = Path(restore_to or backup_meta.get("repo_root")).expanduser().resolve()

    # verify checksum before extracting (defensive)
    expected = backup_meta.get("zip_sha256")
    if expected:
        actual = _sha256_of_file(zip_path)
        if actual != expected:
            return {"status": "error", "error": "checksum_mismatch", "expected": expected, "actual": actual}

    temp_dir = target_root / f".nova_restore_tmp_{uuid.uuid4().hex[:6]}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(temp_dir)
    for root, dirs, files in os.walk(temp_dir):
        rel_root = Path(root).relative_to(temp_dir)
        for d in dirs:
            (target_root / rel_root / d).mkdir(parents=True, exist_ok=True)
        for f in files:
            src = Path(root) / f
            dest = target_root / rel_root / f
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    shutil.rmtree(temp_dir, ignore_errors=True)
    return {"status": "ok", "restored_to": str(target_root)}
