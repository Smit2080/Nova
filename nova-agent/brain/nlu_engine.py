# brain/nlu_engine.py

from sentence_transformers import SentenceTransformer, util
from typing import Dict, Any
import torch
from .nlu_engine_basic import parse_user_message as fallback_engine

# Load model ONCE
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- define semantic intent categories ---
INTENT_EXAMPLES = {
    "research": [
        "research this", "search online", "google it", "find info",
        "internet search", "net pe dekh", "check on web", "look up"
    ],
    "advise": [
        "suggest something", "what should we add", "improve system",
        "kuch aur add kar", "any new features", "how to improve"
    ],
    "dependencies": [
        "missing module", "dependency issue", "packages check",
        "requirements problem", "import error"
    ],
    "performance": [
        "system slow", "optimize", "speed up", "lag ho raha",
        "performance improve"
    ],
    "run_tests": [
        "run tests", "execute test", "syntax check", "validate code"
    ],
    "merge": [
        "apply changes", "merge it", "final kar", "commit work"
    ],
    "safety": [
        "backup", "rollback", "restore", "safe rakhna"
    ],
    "chat": [
        "talk", "chat", "explain", "help me understand"
    ]
}

# Convert to embeddings
INTENT_EMBED = {
    intent: model.encode(examples, convert_to_tensor=True)
    for intent, examples in INTENT_EXAMPLES.items()
}


def detect_intent(text: str) -> Dict[str, Any]:

    """
    Hybrid NLU:
      1. Semantic intent detection using embeddings
      2. Rule engine fallback if confidence is too low
    """

    q = (text or "").strip()
    if not q:
        return {"intent": "chat", "needs_internet": False, "deep_research": False}

    # Semantic embedding
    q_emb = model.encode([q], convert_to_tensor=True)

    best_intent = None
    best_score = -1

    # Compare with each intent cluster
    for intent, emb_list in INTENT_EMBED.items():
        score = util.cos_sim(q_emb, emb_list).max().item()

        if score > best_score:
            best_score = score
            best_intent = intent

    # If low confidence, fallback to basic engine
    if best_score < 0.35:   # threshold tuned for beginners
        return fallback_engine(q)

    # --- extra flags ---
    text_low = q.lower()

    needs_internet = any(w in text_low for w in [
        "research", "google", "search", "internet", "online", "net"
    ])

    deep_research = any(w in text_low for w in [
        "until you find", "jab tak", "keep searching", "deep research"
    ])

    return {
        "intent": best_intent,
        "confidence": float(best_score),
        "needs_internet": needs_internet,
        "deep_research": deep_research
    }
