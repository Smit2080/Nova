# brain/nlu_engine.py

from typing import Dict, Any
import logging

from sentence_transformers import SentenceTransformer, util
from .nlu_engine_basic import parse_user_message as fallback_engine

log = logging.getLogger("nova.nlu")
if not log.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("[%(levelname)s] [NLU] %(message)s"))
    log.addHandler(h)
log.setLevel(logging.INFO)

# --------------------------------------------------
# TRY TO LOAD SEMANTIC MODEL
# --------------------------------------------------
try:
    _SEM_MODEL: SentenceTransformer | None = SentenceTransformer("all-MiniLM-L6-v2")
    log.info("Loaded SentenceTransformer: all-MiniLM-L6-v2")
except Exception as e:
    log.error(f"Failed to load semantic NLU model, falling back to basic NLU only: {e}")
    _SEM_MODEL = None

# --------------------------------------------------
# INTENT EXAMPLES (CLUSTERS)
# --------------------------------------------------
INTENT_EXAMPLES: dict[str, list[str]] = {
    "research": [
        "research this",
        "search online",
        "google it",
        "find info",
        "internet search",
        "net pe dekh",
        "check on web",
        "look up",
    ],
    "advise": [
        "suggest something",
        "what should we add",
        "improve system",
        "kuch aur add kar",
        "any new features",
        "how to improve",
        "advise me on this project",
    ],
    "dependencies": [
        "missing module",
        "dependency issue",
        "packages check",
        "requirements problem",
        "import error",
        "pip packages",
    ],
    "performance": [
        "system slow",
        "optimize",
        "speed up",
        "lag ho raha",
        "performance improve",
        "make this faster",
    ],
    "run_tests": [
        "run tests",
        "execute tests",
        "syntax check",
        "validate code",
        "pytest chalao",
        "check if code is working",
    ],
    "merge": [
        "apply changes",
        "merge it",
        "final kar",
        "commit work",
        "approve merge",
        "push to integrated",
    ],
    "safety": [
        "backup",
        "rollback",
        "restore",
        "safe rakhna",
        "create backup",
        "undo changes",
    ],
    "diagnose_llm": [
        "diagnose llm",
        "run llm diagnostics",
        "check which model you are using",
        "test your models",
        "check brain health",
        "llm status",
    ],
    "builder": [
        "builder mode",
        "auto build this feature",
        "make this ui",
        "generate frontend",
        "generate backend",
        "agent builder",
    ],
    "chat": [
        "talk",
        "chat",
        "explain",
        "help me understand",
        "normal conversation",
        "bata na yaar",
    ],
}

# --------------------------------------------------
# PRECOMPUTE CLUSTER EMBEDDINGS (IF MODEL AVAILABLE)
# --------------------------------------------------
if _SEM_MODEL is not None:
    INTENT_EMBED = {
        intent: _SEM_MODEL.encode(examples, convert_to_tensor=True)
        for intent, examples in INTENT_EXAMPLES.items()
    }
else:
    INTENT_EMBED: dict[str, Any] = {}

# intents where we treat as "code-heavy"
CODE_INTENTS = {
    "code",
    "build",
    "builder",
    "fix",
    "debug",
    "feature",
    "bug",
    "patch",
    "refactor",
    "tests",
    "run_tests",
}

# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def detect_intent(text: str) -> Dict[str, Any]:
    """
    Hybrid NLU:
      1. Try semantic intent clustering (SentenceTransformer).
      2. If model not loaded or low confidence → fall back to basic engine.
    """

    q = (text or "").strip()
    if not q:
        return {
            "intent": "chat",
            "confidence": 0.0,
            "needs_internet": False,
            "deep_research": False,
        }

    # 1) If semantic model is missing, just use your old engine
    if _SEM_MODEL is None or not INTENT_EMBED:
        base = fallback_engine(q)
        # make sure keys exist
        base.setdefault("intent", "chat")
        base.setdefault("confidence", 0.0)
        base.setdefault("needs_internet", False)
        base.setdefault("deep_research", False)
        return base

    # 2) Semantic scoring
    q_emb = _SEM_MODEL.encode([q], convert_to_tensor=True)

    best_intent = None
    best_score = -1.0

    for intent, emb_list in INTENT_EMBED.items():
        score = float(util.cos_sim(q_emb, emb_list).max().item())
        if score > best_score:
            best_score = score
            best_intent = intent

    # 3) If very low confidence → use basic rule engine
    if best_score < 0.35:
        base = fallback_engine(q)
        base.setdefault("intent", "chat")
        base.setdefault("confidence", float(best_score))
        base.setdefault("needs_internet", False)
        base.setdefault("deep_research", False)
        return base

    # 4) Extra flags
    text_low = q.lower()

    needs_internet = any(
        w in text_low
        for w in ["research", "google", "search", "internet", "online", "web", "net pe"]
    )

    deep_research = any(
        w in text_low
        for w in ["until you find", "jab tak", "keep searching", "deep research"]
    )

    result = {
        "intent": best_intent or "chat",
        "confidence": float(best_score),
        "needs_internet": needs_internet,
        "deep_research": deep_research,
    }

    log.info(
        f"NLU → intent={result['intent']} conf={result['confidence']:.3f} "
        f"net={result['needs_internet']} deep={result['deep_research']}"
    )
    return result