# advisor_engine.py
from pathlib import Path
import ast
import json
from typing import List, Dict, Any, Optional


# ---------- 1. BASIC IMPORT SCANNER ----------

def scan_imports(project_root: Path) -> List[str]:
    """
    Scan all .py files under project_root and collect top-level imports.
    This is a simple static analyzer (no execution).
    """
    imports = set()
    if not project_root.exists():
        return []

    for py_file in project_root.rglob("*.py"):
        try:
            text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(text)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    return sorted(imports)


# ---------- 2. INTENT / CATEGORY DETECTION (VERY SIMPLE) ----------

def classify_query(query: str) -> str:
    """
    Very basic intent classification based on keywords.
    We don't rely on exact wording so Hinglish/Marathi/English mix still works
    as long as key English words appear.
    """
    q = (query or "").lower()

    # improvement / suggestion intent
    if any(w in q for w in ["suggest", "improve", "better", "add anything", "aur add", "kuch aur", "feature", "tool"]):
        return "suggest_features"

    # dependency / env intent
    if any(w in q for w in ["dependency", "module", "package", "import", "library", "requirements"]):
        return "dependencies"

    # performance / speed
    if any(w in q for w in ["fast", "slow", "optimize", "performance", "lag", "heavy"]):
        return "performance"

    # safety / backup / version
    if any(w in q for w in ["safe", "backup", "version", "rollback", "crash", "restore"]):
        return "safety"

    # default: generic advice
    return "generic"


# ---------- 3. SUGGESTION GENERATOR ----------

def _suggest_generic_beginner(project_imports: List[str], env_meta: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Suggestions that are generally useful for you as a beginner
    building a Nova-like Builder+Agent.
    """
    suggestions = []

    suggestions.append({
        "id": "logs_basic",
        "title": "Add simple logging to your agent",
        "category": "architecture",
        "difficulty": "easy",
        "impact": "medium",
        "auto_applicable": True,
        "explanation": (
            "Right now your agent prints very little about what it is doing. "
            "Adding a small logging helper will make it easier to debug when something breaks "
            "or when installs/tests fail. This is beginner-friendly and very safe."
        )
    })

    suggestions.append({
        "id": "tests_minimal",
        "title": "Add a minimal test suite for core endpoints",
        "category": "quality",
        "difficulty": "medium",
        "impact": "high",
        "auto_applicable": False,
        "explanation": (
            "You are building a complex system (plan/prepare/apply_patch/run_tests/merge/rollback). "
            "Even 3–5 basic tests (for success + failure cases) will prevent many future bugs. "
            "We can generate test templates automatically later."
        )
    })

    suggestions.append({
        "id": "ui_panel",
        "title": "Create a simple web UI panel for your agent",
        "category": "usability",
        "difficulty": "medium",
        "impact": "high",
        "auto_applicable": False,
        "explanation": (
            "Instead of calling REST endpoints manually, a small React/HTML UI can show "
            "requests, backups, environment info, and suggestions in a friendly way. "
            "Later this UI becomes Nova's main control panel."
        )
    })

    suggestions.append({
        "id": "advisor_integration",
        "title": "Connect advisor to your chat endpoint",
        "category": "intelligence",
        "difficulty": "medium",
        "impact": "high",
        "auto_applicable": True,
        "explanation": (
            "Currently the /chat endpoint only echoes messages and tells you which API to call. "
            "We can integrate this advisor engine so that when you ask things like "
            "'kuch aur add kar sakte?' it automatically returns improvement suggestions."
        )
    })

    # If we know environment packages, add version-related hints
    if env_meta and env_meta.get("pip_packages"):
        pkgs = env_meta["pip_packages"]
        if "fastapi" in pkgs:
            suggestions.append({
                "id": "fastapi_docs",
                "title": "Pin FastAPI and related packages using requirements_pinned.txt",
                "category": "versioning",
                "difficulty": "easy",
                "impact": "high",
                "auto_applicable": True,
                "explanation": (
                    "Your environment uses FastAPI and related libraries. "
                    "Locking their versions (which you already started with requirements_pinned.txt) "
                    "avoids random breakage when upgrading. The advisor can also warn you before "
                    "any risky upgrade."
                )
            })

    return suggestions


def _suggest_dependency_related(project_imports: List[str], env_meta: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    suggestions = []

    installed = set()
    if env_meta and env_meta.get("pip_packages"):
        installed = set(env_meta["pip_packages"].keys())

    # missing = imports that are not in installed list (best-effort; may not be perfect)
    missing = [imp for imp in project_imports if imp not in installed and imp not in ("sys", "os", "pathlib", "json", "typing", "subprocess")]

    if missing:
        suggestions.append({
            "id": "missing_dependencies",
            "title": "Install missing Python packages",
            "category": "dependencies",
            "difficulty": "easy",
            "impact": "high",
            "auto_applicable": True,
            "explanation": (
                f"These imports appear in your code but are not in your current environment: {', '.join(missing)}. "
                "We can auto-create a sandbox venv for the request and install only these packages there, "
                "instead of polluting your global system."
            ),
            "missing_modules": missing
        })
    else:
        suggestions.append({
            "id": "deps_ok",
            "title": "No obvious missing dependencies detected",
            "category": "dependencies",
            "difficulty": "easy",
            "impact": "medium",
            "auto_applicable": False,
            "explanation": (
                "From a quick static scan, all imported modules appear to exist in your environment. "
                "If you still see ImportError at runtime, we can add a deeper checker later."
            )
        })

    return suggestions


def _suggest_performance(env_meta: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    suggestions = []
    suggestions.append({
        "id": "perf_logs",
        "title": "Add simple timing logs around heavy operations",
        "category": "performance",
        "difficulty": "easy",
        "impact": "medium",
        "auto_applicable": True,
        "explanation": (
            "Wrap heavy operations (test runs, large installs, backups) with small timing logs. "
            "This will help you see which part is slow when the project grows."
        )
    })
    suggestions.append({
        "id": "sandbox_limits",
        "title": "Add resource limits for sandbox (CPU/RAM, later via Docker)",
        "category": "performance",
        "difficulty": "hard",
        "impact": "high",
        "auto_applicable": False,
        "explanation": (
            "Limiting CPU/RAM for sandboxed code will keep your main system responsive while Nova runs tests. "
            "This requires either subprocess resource controls or Docker, so we treat it as an advanced step."
        )
    })
    return suggestions


def _suggest_safety(env_meta: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    suggestions = []
    suggestions.append({
        "id": "backup_policy",
        "title": "Define a clear backup/rollback policy",
        "category": "safety",
        "difficulty": "easy",
        "impact": "high",
        "auto_applicable": True,
        "explanation": (
            "You already have backup + rollback endpoints. We should add simple rules like: "
            "'always backup before merge', 'never merge if tests fail', "
            "and 'keep N last backups per project'. This reduces the chance of losing work."
        )
    })
    suggestions.append({
        "id": "version_policy",
        "title": "Add version policy (STRICT / SMART / LATEST)",
        "category": "safety",
        "difficulty": "medium",
        "impact": "high",
        "auto_applicable": False,
        "explanation": (
            "A small config (e.g. config.json) can define whether Nova should always use pinned versions, "
            "allow minor upgrades, or try newer versions. This protects you from surprise breakages "
            "when dependencies change."
        )
    })
    return suggestions


def generate_advice(query: str,
                    project_root: Path,
                    env_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main entry for Advisor Engine.

    - query: natural language question ("kuch aur add kar sakte?", "can we improve anything?")
    - project_root: usually BASE / 'integrated'
    - env_meta: optional environment metadata dict (from environment_<id>.meta.json)
    """
    intent = classify_query(query)
    imports = scan_imports(project_root)

    suggestions: List[Dict[str, Any]] = []

    # always include some beginner-friendly generic suggestions
    suggestions.extend(_suggest_generic_beginner(imports, env_meta))

    if intent == "dependencies":
        suggestions.extend(_suggest_dependency_related(imports, env_meta))
    elif intent == "performance":
        suggestions.extend(_suggest_performance(env_meta))
    elif intent == "safety":
        suggestions.extend(_suggest_safety(env_meta))
    elif intent == "suggest_features":
        # for feature-suggestion queries, mix all categories a bit
        suggestions.extend(_suggest_dependency_related(imports, env_meta))
        suggestions.extend(_suggest_performance(env_meta))
        suggestions.extend(_suggest_safety(env_meta))
    # intent == "generic" -> only generic + maybe later we add more

    return {
        "intent": intent,
        "imports_detected": imports,
        "suggestions": suggestions
    }
