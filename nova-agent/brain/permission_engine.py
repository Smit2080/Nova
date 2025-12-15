# brain/permission_engine.py

from typing import Dict

def check_internet_access(needs_internet: bool, deep_research: bool, has_prior_approval: bool) -> Dict:
    """
    Decides whether AI can use the internet.
    """

    if not needs_internet:
        return {"allowed": False}

    if deep_research and not has_prior_approval:
        return {
            "ask": True,
            "prompt": "Deep research requested. Do you want me to continue researching until I find the answer?"
        }

    if not has_prior_approval:
        return {
            "ask": True,
            "prompt": "Internet access needed — should I proceed?"
        }

    return {"allowed": True}
