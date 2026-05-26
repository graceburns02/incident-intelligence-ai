from __future__ import annotations

import json
import os
from datetime import datetime

SEVERITY_MAP = {
    "sev0": "critical",
    "sev1": "high",
    "sev2": "medium",
    "sev3": "low",
    "p0": "critical",
    "p1": "high",
    "p2": "medium",
    "p3": "low",
    "blocker": "critical",
}


def normalize_severity(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return SEVERITY_MAP.get(normalized, normalized)


def get_openai_api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY")


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def safe_json_loads(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise
