# brain/llm_client.py
import os
import logging
from typing import List, Dict, Any, Optional

import httpx
from groq import Groq
from dotenv import load_dotenv

# --------------------------------------------------
# LOAD .env FIRST
# --------------------------------------------------
load_dotenv()

log = logging.getLogger("nova.llm")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    log.addHandler(handler)
log.setLevel(logging.INFO)

# --------------------------------------------------
# ENV + PROVIDER CONFIG
# --------------------------------------------------

# ---- Groq (PRIMARY) ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_FAST = os.getenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
GROQ_MODEL_SMART = os.getenv("GROQ_MODEL_SMART", "llama-3.3-70b-versatile")  # Updated model

# ---- DeepSeek (SECONDARY) ----
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL_CHAT = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_MODEL_REASON = os.getenv("DEEPSEEK_REASON_MODEL", "deepseek-reasoner")

# ---- OpenRouter (THIRD) ----
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")

# ---- LM Studio (LOCAL TIER-4) ----
LMSTUDIO_ENABLED = os.getenv("LMSTUDIO_ENABLED", "false").lower() == "true"
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "local-model")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "")

# ---- Ollama (LOCAL TIER-4) ----
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL_FAST = os.getenv("OLLAMA_MODEL_FAST", "llama3.2:3b")
OLLAMA_MODEL_SMART = os.getenv("OLLAMA_MODEL_SMART", "llama3.1:8b")

# ---- Behavior Flags ----
FORCE_LOCAL_FOR_HEAVY = os.getenv("FORCE_LOCAL_FOR_HEAVY", "false").lower() == "true"
TIER3_LLM_OVERRIDE = os.getenv("TIER3_LLM_OVERRIDE", "").strip().lower()

# ---- Provider Availability ----
HAS_GROQ = bool(GROQ_API_KEY)
HAS_DEEPSEEK = bool(DEEPSEEK_API_KEY)
HAS_OPENROUTER = bool(OPENROUTER_API_KEY)
HAS_LMSTUDIO = LMSTUDIO_ENABLED
HAS_OLLAMA = OLLAMA_ENABLED

if not (HAS_GROQ or HAS_DEEPSEEK or HAS_OPENROUTER or HAS_LMSTUDIO or HAS_OLLAMA):
    raise ValueError("❌ No LLM provider configured in .env")

# Groq client
groq_client: Optional[Groq] = Groq(api_key=GROQ_API_KEY) if HAS_GROQ else None

# --------------------------------------------------
# ROLE NORMALIZATION
# --------------------------------------------------
def normalize_role(role: str) -> str:
    if role in ("user", "assistant", "system"):
        return role
    if role == "agent":
        return "assistant"
    return "user"

# --------------------------------------------------
# HEAVY WORK DETECTION
# --------------------------------------------------
CODE_INTENTS = {
    "code", "build", "fix", "debug", "feature",
    "bug", "patch", "refactor", "tests", "run_tests",
}

def is_heavy_code(user_text: str, intent: Optional[str]) -> bool:
    text = user_text.lower()
    return (
        len(user_text) > 800
        or "```" in user_text
        or "traceback" in text
        or any(w in text for w in ["error", "exception", "stack", "crash"])
        or (intent in CODE_INTENTS)
    )

# --------------------------------------------------
# PROVIDER CALLS
# --------------------------------------------------
def call_groq(model: str, messages: List[Dict[str, str]]) -> str:
    if not groq_client:
        raise RuntimeError("Groq client not loaded")

    log.info(f"[LLM] Groq → {model}")

    resp = groq_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
    )
    return resp.choices[0].message.content


def call_deepseek(model: str, messages: List[Dict[str, str]]) -> str:
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages, "stream": False}

    log.info(f"[LLM] DeepSeek → {model}")
    r = httpx.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()

    return r.json()["choices"][0]["message"]["content"]


def call_openrouter(model: str, messages: List[Dict[str, str]]) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nova.local",
        "X-Title": "Nova Builder+Agent",
    }
    payload = {"model": model, "messages": messages}

    log.info(f"[LLM] OpenRouter → {model}")
    r = httpx.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()

    return r.json()["choices"][0]["message"]["content"]


def call_lmstudio(model: str, messages: List[Dict[str, str]]) -> str:
    base = LMSTUDIO_BASE_URL.rstrip("/")
    url = f"{base}/chat/completions"

    headers = {"Content-Type": "application/json"}
    if LMSTUDIO_API_KEY:
        headers["Authorization"] = f"Bearer {LMSTUDIO_API_KEY}"

    payload = {"model": model, "messages": messages}

    log.info(f"[LLM] LMStudio → {model}")
    r = httpx.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()

    return r.json()["choices"][0]["message"]["content"]


def call_ollama(model: str, messages: List[Dict[str, str]]) -> str:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {"model": model, "messages": messages}

    log.info(f"[LLM] Ollama → {model}")
    r = httpx.post(url, json=payload, timeout=120)
    r.raise_for_status()

    data = r.json()
    return data.get("message", {}).get("content") or data["choices"][0]["message"]["content"]

# --------------------------------------------------
# BUILD MESSAGES
# --------------------------------------------------
def build_messages(user_text: str, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    msgs = [{
        "role": "system",
        "content": (
            "You are Nova Builder+Agent.\n"
            "- You write, debug, modify code.\n"
            "- You reason step-by-step for complex tasks.\n"
            "- Prefer safe minimal edits.\n"
            "- If needed, ask for clarification first."
        )
    }]

    for msg in history[-10:]:
        role = normalize_role(msg.get("role", "user"))
        if msg.get("message"):
            msgs.append({"role": role, "content": msg["message"]})

    msgs.append({"role": "user", "content": user_text})
    return msgs

# --------------------------------------------------
# MAIN ROUTER
# --------------------------------------------------
def chat_with_builder(user_text: str, intent: Optional[str], history: List[Dict[str, Any]]) -> str:
    messages = build_messages(user_text, history)
    heavy = is_heavy_code(user_text, intent)
    log.info(f"[ROUTER] intent={intent} heavy={heavy}")

    # Tier-4 local
    local = []
    if HAS_LMSTUDIO: local.append(("lmstudio", "smart"))
    if HAS_OLLAMA: local.append(("ollama", "smart" if heavy else "fast"))

    # Tier-1/2/3 remote
    remote = []

    # Groq primary
    if HAS_GROQ:
        remote.append(("groq", "smart" if heavy else "fast"))

    # DeepSeek secondary
    if HAS_DEEPSEEK:
        if heavy:
            remote.append(("deepseek", "reason"))
        remote.append(("deepseek", "chat"))

    # OpenRouter third
    if HAS_OPENROUTER:
        remote.append(("openrouter", "smart"))

    # Routing logic
    candidates = []

    if FORCE_LOCAL_FOR_HEAVY and heavy:
        candidates += local + remote
    else:
        candidates += remote + local

    # Provider override
    if TIER3_LLM_OVERRIDE:
        provider = TIER3_LLM_OVERRIDE
        candidates.sort(key=lambda x: 0 if x[0] == provider else 1)

    # Run pipeline
    last_error = None

    for provider, variant in candidates:
        try:
            if provider == "groq":
                model = GROQ_MODEL_SMART if variant == "smart" else GROQ_MODEL_FAST
                return call_groq(model, messages)

            elif provider == "deepseek":
                model = DEEPSEEK_MODEL_REASON if variant == "reason" else DEEPSEEK_MODEL_CHAT
                return call_deepseek(model, messages)

            elif provider == "openrouter":
                return call_openrouter(OPENROUTER_MODEL, messages)

            elif provider == "lmstudio":
                return call_lmstudio(LMSTUDIO_MODEL, messages)

            elif provider == "ollama":
                m = OLLAMA_MODEL_SMART if variant == "smart" else OLLAMA_MODEL_FAST
                return call_ollama(m, messages)

        except Exception as e:
            last_error = e
            log.error(f"[LLM ROUTER] Provider {provider}/{variant} failed: {e}")

    return f"LLM error: {last_error}"