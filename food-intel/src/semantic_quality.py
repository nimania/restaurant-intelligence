from __future__ import annotations

import re

SEMANTIC_REPAIR_ISSUES = {
    "brand-literal-mars",
    "brand-literal-juice-it-up",
    "idiom-literal-zeroes-in",
    "idiom-literal-taps",
    "idiom-literal-footprint",
    "literal-market-reset",
    "literal-gen-z",
}


def diagnose_semantics(item: dict) -> tuple[list[str], int]:
    source_title = str(item.get("title") or "")
    source_summary = str(item.get("summary") or "")
    source = f"{source_title} {source_summary}".lower()
    target_title = str(item.get("title_fa") or "")
    target = " ".join(
        str(item.get(key) or "")
        for key in ("title_fa", "summary_fa", "narrative_fa", "report_fa")
    )
    issues: list[str] = []
    penalty = 0

    def add(condition: bool, issue: str, points: int) -> None:
        nonlocal penalty
        if condition and issue not in issues:
            issues.append(issue)
            penalty += points

    add(bool(re.search(r"\bmars\b", source)) and "مریخ" in target, "brand-literal-mars", 42)
    add("juice it up" in source and bool(re.search(r"آب (?:آن|این) را بالا", target)), "brand-literal-juice-it-up", 45)
    add(("zeroes in on" in source or "zeros in on" in source) and "صفر" in target_title, "idiom-literal-zeroes-in", 42)
    add(bool(re.search(r"\btaps\b", source_title, re.I)) and bool(re.search(r"می(?:‌| )زند|ضربه", target_title)), "idiom-literal-taps", 34)
    add("footprint" in source_title.lower() and "ردپا" in target_title, "idiom-literal-footprint", 28)
    add("beverage alcohol reset" in source and "تنظیم مجدد" in target, "literal-market-reset", 28)
    add("gen z" in source and bool(re.search(r"جنرال\s*Z|ژنرال\s*Z", target, re.I)), "literal-gen-z", 36)

    return issues, min(penalty, 70)
