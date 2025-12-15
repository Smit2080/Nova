# brain/nlu_engine_basic.py

from typing import Dict, Any

def parse_user_message(text: str) -> Dict[str, Any]:
    """
    Simple rule-based fallback NLU.
    This runs when semantic model confidence is low.
    """

    q = (text or "").lower()

    intent = "chat"
    needs_internet = False
    deep_research = False

    # deep research signals
    if any(p in q for p in [
        "research until",
        "jab tak",
        "keep searching",
        "deep research"
    ]):
        return {
            "intent": "research",
            "needs_internet": True,
            "deep_research": True
        }

    # research/internet
    if any(w in q for w in [
        "research", "google", "search", "internet", "online", "net"
    ]):
        intent = "research"
        needs_internet = True

    # suggestions
    if any(w in q for w in [
        "suggest", "improve", "feature", "tool",
        "kuch aur", "add anything", "aur kya"
    ]):
        intent = "advise"

    # dependencies
    if any(w in q for w in [
        "dependency", "module", "package", "import error", "requirements"
    ]):
        intent = "dependencies"

    # performance
    if any(w in q for w in [
        "slow", "fast", "lag", "optimize", "performance"
    ]):
        intent = "performance"

    # tests
    if any(w in q for w in [
        "test", "syntax", "validate", "run test"
    ]):
        intent = "run_tests"

    # merge
    if any(w in q for w in [
        "merge", "apply changes", "commit"
    ]):
        intent = "merge"

    # safety
    if any(w in q for w in [
        "backup", "rollback", "restore", "safe"
    ]):
        intent = "safety"

    return {
        "intent": intent,
        "needs_internet": needs_internet,
        "deep_research": deep_research
    }
