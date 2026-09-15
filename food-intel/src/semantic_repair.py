from __future__ import annotations

from semantic_quality import SEMANTIC_REPAIR_ISSUES, diagnose_semantics
from translation_quality import assess_item

WARN_REPAIR = {
    "long-sentence",
    "very-long-sentence",
    "repetition",
    "too-much-latin",
    "mixed-script",
}


def combined_quality(item: dict) -> dict:
    quality = assess_item(item)
    semantic_issues, penalty = diagnose_semantics(item)
    issues = sorted(set((quality.get("issues") or []) + semantic_issues))
    score = max(0, int(quality.get("score") or 0) - penalty)
    status = quality.get("status", "block")
    if set(semantic_issues) & SEMANTIC_REPAIR_ISSUES:
        status = "retry" if score >= 45 else "block"
    elif semantic_issues and status == "pass":
        status = "warn"
    return {
        **quality,
        "version": 2,
        "score": score,
        "status": status,
        "publishable": status in {"pass", "warn"},
        "issues": issues,
        "semantic_penalty": penalty,
    }


def needs_repair(item: dict) -> bool:
    quality = item.get("translation_quality") or combined_quality(item)
    issues = set(quality.get("issues") or [])
    if issues & SEMANTIC_REPAIR_ISSUES:
        return True
    return quality.get("status") == "warn" and bool(issues & WARN_REPAIR)
