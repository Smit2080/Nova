# brain/__init__.py

from .nlu_engine import detect_intent
from .permission_engine import check_internet_access

__all__ = ["detect_intent", "check_internet_access"]
