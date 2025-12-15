# brain/builder_engine.py

import json
import uuid
from datetime import datetime
from pathlib import Path

from backup_manager import create_backup
from env_manager import capture_environment
from .llm_client import chat_with_builder

# Base paths (same style as app.py)
BASE = Path(__file__).resolve().parent.parent
WORKSPACE = BASE / "workspace"
REQUESTS = BASE / "requests"
BACKUPS = BASE / "backups"
INTEGRATED = BASE / "integrated"

for d in (WORKSPACE, REQUESTS, BACKUPS):
    d.mkdir(parents=True, exist_ok=True)


def run_builder_pipeline(
    instruction: str,
    existing_request_id: str | None = None,
) -> dict:
    """
    First version of the Builder workflow.

    For now it:
      - creates or reuses a request_id
      - creates a workspace folder
      - creates a zip backup of integrated/
      - captures environment metadata
      - asks the LLM for a build plan / strategy

    Later we will extend this to:
      - fetch relevant files
      - ask LLM for concrete file patches
      - write patches into workspace
      - run tests
      - auto-fix loop
      - ask for merge approval
    """
    instruction = (instruction or "").strip()
    if not instruction:
        raise ValueError("instruction is required")

    request_id = existing_request_id or uuid.uuid4().hex[:8]

    # 1) Workspace
    ws = WORKSPACE / request_id
    ws.mkdir(parents=True, exist_ok=True)

    # 2) Backup integrated/ before changes
    backup_meta = create_backup(
        request_id=request_id,
        targets=[],
        repo_root=INTEGRATED,
        note=f"auto-build backup for: {instruction}",
    )

    # 3) Capture environment metadata
    backup_dir = Path(backup_meta["zip_path"]).parent
    env_meta = capture_environment(
        request_id=request_id,
        dest_dir=backup_dir,
    )

    # 4) Save a lightweight builder record
    record = {
        "request_id": request_id,
        "instruction": instruction,
        "workspace": str(ws),
        "backup": backup_meta,
        "env_meta": env_meta,
        "created": datetime.utcnow().isoformat(),
        "status": "planned",
    }
    (REQUESTS / f"{request_id}.builder.json").write_text(
        json.dumps(record, indent=2),
        encoding="utf-8",
    )

    # 5) Ask LLM for a build plan / strategy (no code yet)
    #    We treat this as a builder_planning intent.
    history: list[dict] = []
    intent = "builder_plan"

    plan_text = chat_with_builder(
        text=instruction,
        intent=intent,
        history=history,
   )

    return {
        "request_id": request_id,
        "instruction": instruction,
        "plan_text": plan_text,
        "backup": backup_meta,
        "env_meta": env_meta,
        "workspace": str(ws),
    }