from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid, os, json, shutil
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()
from brain.tools_engine import list_tools, run_tool

from backup_manager import create_backup, list_backups, restore_backup
from env_manager import capture_environment
from advisor_engine import generate_advice
from brain.nlu_engine import detect_intent
from brain.permission_engine import check_internet_access
from brain.llm_client import chat_with_builder
from brain.builder_engine import run_builder_pipeline

# ❌ REMOVE THIS LINE IF YOU HAVE IT BELOW AGAIN
app = FastAPI(title="Nova Builder-Agent (Starter)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# PATHS / DIRS
# -------------------------
BASE = Path(__file__).resolve().parent
WORKSPACE = BASE / "workspace"
REQUESTS = BASE / "requests"
BACKUPS = BASE / "backups"
CHAT_DIR = BASE / "chat_sessions"

for d in (WORKSPACE, REQUESTS, BACKUPS, CHAT_DIR):
    d.mkdir(parents=True, exist_ok=True)


# -----------------------------------
# PLAN REQUEST
# -----------------------------------
class PlanRequest(BaseModel):
    code: str
    path: str
    intent: str | None = None


class AutoBuildRequest(BaseModel):
    code: str
    path: str
    intent: str | None = None


class AIChange(BaseModel):
    path: str           # file path relative inside workspace
    code: str           # full file content
    intent: str | None = None  # optional tag like "feature: login"


class AIRequest(BaseModel):
    instruction: str             # high-level instruction
    changes: list[AIChange]      # list of file modifications from AI


class BuilderRunRequest(BaseModel):
    instruction: str
    request_id: str | None = None  # allow re-using same build session later

@app.post("/plan")
def plan(req: PlanRequest):
    request_id = uuid.uuid4().hex[:8]

    plan_data = {
        "request_id": request_id,
        "intent": req.intent or "integrate code",
        "plan": [
            f"create workspace for {req.path}",
            f"backup target files for {req.path}",
            "write code into sandbox",
            "run syntax tests",
            "ask for approval to merge",
        ],
        "created": datetime.utcnow().isoformat(),
    }

    with open(REQUESTS / f"{request_id}.plan.json", "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2)

    return plan_data


# -----------------------------------
# PREPARE WORKSPACE + BACKUP META
# -----------------------------------
@app.post("/prepare")
def prepare(body: dict):
    request_id = body.get("request_id") or uuid.uuid4().hex[:8]

    # create workspace for sandbox testing
    ws = WORKSPACE / request_id
    ws.mkdir(parents=True, exist_ok=True)

    # create a real zip backup of the current integrated/ folder (safe)
    repo_root = BASE / "integrated"
    backup_meta = create_backup(
        request_id=request_id,
        targets=[],
        repo_root=repo_root,
        note="backup before integrate",
    )

    # capture environment metadata (pip freeze, python version, node)
    backup_dir = Path(backup_meta["zip_path"]).parent
    env_meta = capture_environment(request_id=request_id, dest_dir=backup_dir)

    # write pinned requirements.txt from pip_freeze_lines (if available)
    req_lines = env_meta.get("pip_freeze_lines", []) or []
    if req_lines:
        req_path = backup_dir / "requirements_pinned.txt"
        with open(req_path, "w", encoding="utf-8") as rf:
            rf.write("\n".join(req_lines))
        env_meta["requirements_pinned"] = str(req_path)

    # save a lightweight request record as well
    req_record = {
        "request_id": request_id,
        "workspace": str(ws),
        "backup": backup_meta,
        "env_meta": env_meta,
        "created": datetime.utcnow().isoformat(),
    }
    with open(REQUESTS / f"{request_id}.req.json", "w", encoding="utf-8") as f:
        json.dump(req_record, f, indent=2)

    return {
        "request_id": request_id,
        "status": "prepared",
        "detail": "workspace & zip backup created",
        "backup": backup_meta,
        "env_meta": env_meta,
    }


# -----------------------------------
# APPLY PATCH (WRITE CODE INTO WORKSPACE)
# -----------------------------------
@app.post("/apply_patch")
def apply_patch(body: dict):
    request_id = body.get("request_id")
    if not request_id:
        raise HTTPException(status_code=400, detail="request_id required")

    ws = WORKSPACE / request_id
    if not ws.exists():
        raise HTTPException(status_code=404, detail="workspace not found")

    path = body.get("path")
    code = body.get("code", "")

    full_path = ws / path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(code)

    return {
        "request_id": request_id,
        "status": "applied",
        "detail": f"file {path} written to workspace",
    }


# -----------------------------------
# RUN TESTS (SYNTAX CHECK)
# -----------------------------------
@app.post("/run_tests")
def run_tests(body: dict):
    import subprocess

    request_id = body.get("request_id")
    if not request_id:
        raise HTTPException(status_code=400, detail="request_id required")

    ws = WORKSPACE / request_id
    if not ws.exists():
        raise HTTPException(status_code=404, detail="workspace not found")

    script = ["python", str(BASE / "sandbox" / "run_tests.py"), str(ws)]

    try:
        proc = subprocess.run(
            script,
            capture_output=True,
            text=True,
            timeout=30,
        )
        ok = proc.returncode == 0
        output = proc.stdout + "\n" + proc.stderr
        return {
            "request_id": request_id,
            "status": "passed" if ok else "failed",
            "detail": output,
        }

    except Exception as e:
        return {"request_id": request_id, "status": "error", "detail": str(e)}


# -----------------------------------
# MERGE (DEMO VERSION)
# -----------------------------------
@app.post("/merge")
def merge(body: dict):
    request_id = body.get("request_id")
    if not request_id:
        raise HTTPException(status_code=400, detail="request_id required")

    ws = WORKSPACE / request_id
    integrated = BASE / "integrated"

    if not ws.exists():
        raise HTTPException(status_code=404, detail="workspace not found")

    integrated.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(ws):
        for f in files:
            src = Path(root) / f
            rel = src.relative_to(ws)
            dest = integrated / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    return {"request_id": request_id, "status": "merged", "detail": "workspace copied to integrated/"}


# -----------------------------------
# ROLLBACK
# -----------------------------------
@app.post("/rollback")
def rollback(body: dict):
    request_id = body.get("request_id")
    if not request_id:
        raise HTTPException(status_code=400, detail="request_id required")

    backups = list_backups(request_id)
    if not backups:
        ws = WORKSPACE / request_id
        if ws.exists():
            shutil.rmtree(ws)
        return {
            "request_id": request_id,
            "status": "rolled_back",
            "detail": "no backup found; workspace removed",
        }

    backup_meta = backups[0]
    restore_res = restore_backup(backup_meta, restore_to=str(BASE / "integrated"))

    ws = WORKSPACE / request_id
    if ws.exists():
        shutil.rmtree(ws)

    return {"request_id": request_id, "status": "restored", "detail": restore_res}


# -----------------------------------
# BACKUP LIST & MANUAL RESTORE ENDPOINTS
# -----------------------------------
@app.get("/backups/{request_id}")
def list_backups_endpoint(request_id: str):
    b = list_backups(request_id)
    return {"request_id": request_id, "backups": b}


@app.post("/restore")
def restore_endpoint(body: dict):
    request_id = body.get("request_id")
    backup_id = body.get("backup_id")
    if not request_id or not backup_id:
        raise HTTPException(status_code=400, detail="request_id and backup_id required")

    backups = list_backups(request_id)
    match = None
    for b in backups:
        if b.get("backup_id") == backup_id:
            match = b
            break

    if not match:
        raise HTTPException(status_code=404, detail="backup not found for this request_id")

    restore_res = restore_backup(match, restore_to=str(BASE / "integrated"))

    return {
        "request_id": request_id,
        "backup_id": backup_id,
        "status": "restored",
        "detail": restore_res,
    }


@app.get("/env/{request_id}")
def get_env_metadata(request_id: str):
    d = BACKUPS / request_id
    if not d.exists():
        raise HTTPException(status_code=404, detail="request_id not found")

    candidate = d / f"environment_{request_id}.meta.json"
    if candidate.exists():
        return {
            "request_id": request_id,
            "env_meta": json.load(open(candidate, "r", encoding="utf-8")),
        }

    for p in sorted(d.glob("environment_*.meta.json"), reverse=True):
        try:
            return {
                "request_id": request_id,
                "env_meta": json.load(open(p, "r", encoding="utf-8")),
            }
        except Exception:
            continue

    raise HTTPException(status_code=404, detail="env metadata not found")


# -----------------------------------
# ADVISOR ENDPOINT
# -----------------------------------
@app.post("/advise")
def advise(body: dict):
    query = body.get("query", "")
    request_id = body.get("request_id")

    env_meta = None
    if request_id:
        d = BACKUPS / request_id
        env_file = d / f"environment_{request_id}.meta.json"
        if env_file.exists():
            try:
                env_meta = json.load(open(env_file, "r", encoding="utf-8"))
            except Exception:
                env_meta = None

    project_root = BASE / "integrated"

    advice = generate_advice(query=query, project_root=project_root, env_meta=env_meta)
    return {
        "query": query,
        "intent": advice["intent"],
        "imports_detected": advice["imports_detected"],
        "suggestions": advice["suggestions"],
    }

# -----------------------------------
# TOOLS API (Safe OS toolkit)
# -----------------------------------

@app.get("/tools")
def tools_catalog():
    """
    List all available tools that Nova can use.
    Safe to call from UI or LLM.
    """
    return list_tools()


@app.post("/tools/run")
def tools_run(body: dict):
    """
    Run a single tool in SAFE MODE.

    Body:
    {
      "tool": "read_file",
      "args": { ... },
      "confirm": false   // for dangerous tools, must be true to actually execute
    }
    """
    tool_name = body.get("tool")
    args = body.get("args") or {}
    confirm = bool(body.get("confirm", False))

    if not tool_name:
        raise HTTPException(status_code=400, detail="tool is required")

    result = run_tool(tool_name, args, confirm=confirm)
    return result

# -----------------------------------
# AI INTERFACE ENDPOINT
# -----------------------------------
@app.post("/ai_interface")
def ai_interface(req: AIRequest = Body(...)):
    request_id = uuid.uuid4().hex[:8]

    ws = WORKSPACE / request_id
    ws.mkdir(parents=True, exist_ok=True)

    repo_root = BASE / "integrated"
    backup_meta = create_backup(
        request_id=request_id,
        targets=[],
        repo_root=repo_root,
        note=f"auto-build backup for {req.instruction}",
    )

    import subprocess
    for change in req.changes:
        path = ws / change.path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(change.code)

    script = ["python", str(BASE / "sandbox" / "run_tests.py"), str(ws)]
    proc = subprocess.run(script, capture_output=True, text=True, timeout=30)
    tests_ok = proc.returncode == 0
    test_output = proc.stdout + "\n" + proc.stderr

    return {
        "request_id": request_id,
        "instruction": req.instruction,
        "tests_passed": tests_ok,
        "test_output": test_output,
        "backup": backup_meta,
        "message": (
            "Tests passed! Approve merge? Use /merge"
            if tests_ok
            else "Tests failed — fix code or adjust patches."
        ),
    }

@app.post("/builder/run")
def builder_run(req: BuilderRunRequest):
    """
    High-level Builder entrypoint.

    It will:
      - create/reuse a request_id
      - create workspace
      - backup integrated/
      - capture env metadata
      - ask the LLM for a build plan (no code changes yet)
    """
    try:
        result = run_builder_pipeline(
            instruction=req.instruction,
            existing_request_id=req.request_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------
# LLM DIAGNOSTIC ENDPOINT + FUNCTION
# -----------------------------------
import time
from brain.llm_client import (
    call_groq,
    call_deepseek,
    call_openrouter,
    call_lmstudio,
    call_ollama,
    HAS_GROQ,
    HAS_DEEPSEEK,
    HAS_OPENROUTER,
    HAS_LMSTUDIO,
    HAS_OLLAMA,
    GROQ_MODEL_FAST,
    GROQ_MODEL_SMART,
    DEEPSEEK_MODEL_CHAT,
    DEEPSEEK_MODEL_REASON,
    OPENROUTER_MODEL,
    LMSTUDIO_MODEL,
    OLLAMA_MODEL_FAST,
    OLLAMA_MODEL_SMART,
)

TEST_MESSAGE = [{"role": "user", "content": "Diagnostic test"}]

def test_provider(name, func, *args):
    try:
        start = time.perf_counter()
        func(*args, TEST_MESSAGE)
        end = time.perf_counter()
        return {"status": "PASS", "latency_ms": int((end - start) * 1000)}
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}

@app.post("/diagnose_llm")
def diagnose_llm():
    results = {}

    # Primary: Groq
    if HAS_GROQ:
        results["groq_fast"] = test_provider("groq_fast", call_groq, GROQ_MODEL_FAST)
        results["groq_smart"] = test_provider("groq_smart", call_groq, GROQ_MODEL_SMART)
    else:
        results["groq_fast"] = {"status": "DISABLED"}
        results["groq_smart"] = {"status": "DISABLED"}

    # Secondary: DeepSeek
    if HAS_DEEPSEEK:
        results["deepseek_chat"] = test_provider("deepseek_chat", call_deepseek, DEEPSEEK_MODEL_CHAT)
        results["deepseek_reason"] = test_provider("deepseek_reason", call_deepseek, DEEPSEEK_MODEL_REASON)
    else:
        results["deepseek_chat"] = {"status": "DISABLED"}
        results["deepseek_reason"] = {"status": "DISABLED"}

    # Third: OpenRouter
    if HAS_OPENROUTER:
        results["openrouter"] = test_provider("openrouter", call_openrouter, OPENROUTER_MODEL)
    else:
        results["openrouter"] = {"status": "DISABLED"}

    # Local: LM Studio
    if HAS_LMSTUDIO:
        results["lmstudio"] = test_provider("lmstudio", call_lmstudio, LMSTUDIO_MODEL)
    else:
        results["lmstudio"] = {"status": "DISABLED"}

    # Local: Ollama
    if HAS_OLLAMA:
        results["ollama_fast"] = test_provider("ollama_fast", call_ollama, OLLAMA_MODEL_FAST)
        results["ollama_smart"] = test_provider("ollama_smart", call_ollama, OLLAMA_MODEL_SMART)
    else:
        results["ollama_fast"] = {"status": "DISABLED"}
        results["ollama_smart"] = {"status": "DISABLED"}

    return {"providers": results}


async def run_llm_diagnostics():
    """Call the same logic as REST endpoint but usable inside chat."""
    return diagnose_llm()

# -----------------------------------
# CHAT ENDPOINTS (FINAL MERGED VERSION)
# -----------------------------------
def _session_file(session_id: str):
    return CHAT_DIR / f"{session_id}.json"


@app.post("/chat")
async def chat(req: Request):
    data = await req.json()
    session_id = data.get("session_id") or uuid.uuid4().hex[:8]
    role = data.get("role", "user")
    message = data.get("message", "")
    request_id = data.get("request_id")

    sf = _session_file(session_id)

    # Load session history
    if sf.exists():
        history = json.load(open(sf, "r", encoding="utf-8"))
    else:
        history = []

    # Append user message
    history.append(
        {
            "role": role,
            "message": message,
            "ts": datetime.utcnow().isoformat(),
        }
    )

    # Run NLU
    analysis = detect_intent(message)
    intent = analysis.get("intent")
    needs_internet = analysis.get("needs_internet")
    deep_research = analysis.get("deep_research")
    confidence = analysis.get("confidence")

    # ------------------------------
    # NATURAL LANGUAGE: DIAGNOSE LLM
    # ------------------------------
    if intent == "diagnose_llm":
        results = await run_llm_diagnostics()
        formatted = json.dumps(results, indent=2)
        reply = f"📊 **LLM Diagnostic Report**\n```\n{formatted}\n```"

        # Store reply
        history.append(
            {
                "role": "agent",
                "message": reply,
                "ts": datetime.utcnow().isoformat(),
            }
        )
        with open(sf, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        return {"session_id": session_id, "reply": reply}

    reply = ""

    # ------------------------------
    # INTERNET PERMISSION REQUESTS
    # ------------------------------
    if needs_internet:
        perm = check_internet_access(
            needs_internet=needs_internet,
            deep_research=deep_research,
            has_prior_approval=False,
        )

        if perm.get("ask"):
            reply = perm["prompt"]
        elif perm.get("allowed"):
            reply = "Internet access allowed — online research not wired yet."
        else:
            reply = "Internet access denied."

    # ------------------------------
    # ADVISOR ENGINE
    # ------------------------------
    elif intent in (
        "advise",
        "dependencies",
        "performance",
        "research_performance",
        "safety",
    ):

        env_meta = None

        if request_id:
            d = BACKUPS / request_id
            env_file = d / f"environment_{request_id}.meta.json"
            if env_file.exists():
                try:
                    env_meta = json.load(open(env_file, "r", encoding="utf-8"))
                except Exception:
                    env_meta = None

        project_root = BASE / "integrated"

        advice = generate_advice(
            query=message,
            project_root=project_root,
            env_meta=env_meta,
        )

        suggestions = advice.get("suggestions", [])

        if not suggestions:
            reply = "I analysed your system but found no suggestions."
        else:
            tops = suggestions[:3]
            lines = [f"- {s['title']} ({s['category']})" for s in tops]

            reply = (
                f"Intent: {advice['intent']}\n"
                "Top suggestions:\n"
                + "\n".join(lines)
                + "\nSelect any (1/2/3) to apply."
            )

    # ------------------------------
    # LLM BRAIN (Nova Builder+Agent)
    # ------------------------------
    else:
        reply = chat_with_builder(message, intent, history)

    # Append agent message
    history.append(
        {
            "role": "agent",
            "message": reply,
            "ts": datetime.utcnow().isoformat(),
        }
    )

    # Save session
    with open(sf, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return {"session_id": session_id, "reply": reply}

@app.get("/chat/{session_id}")
def get_chat(session_id: str):
    sf = _session_file(session_id)
    if not sf.exists():
        return {"session_id": session_id, "history": []}
    return {
        "session_id": session_id,
        "history": json.load(open(sf, "r", encoding="utf-8")),
    }