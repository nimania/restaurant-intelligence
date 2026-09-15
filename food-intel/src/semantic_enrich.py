from __future__ import annotations

import json
import re
from pathlib import Path

from quality_enrich import _quarantine, retry_item
from semantic_quality import SEMANTIC_REPAIR_ISSUES
from semantic_repair import combined_quality, needs_repair
from translate_fa import PersianTranslator, looks_persian

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "news.json"
TEXT_FIELDS = ("title_fa", "summary_fa", "report_fa", "narrative_fa")


def _replace_fields(item: dict, pattern: str, replacement: str) -> int:
    changed = 0
    for field in TEXT_FIELDS:
        value = str(item.get(field) or "")
        if not value:
            continue
        updated = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        if updated != value:
            item[field] = updated
            changed += 1
    return changed


def direct_semantic_repairs(item: dict) -> int:
    """Repair deterministic mistranslations only when the English source proves intent."""
    source = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    changed = 0

    if re.search(r"\bmars\b", source):
        changed += _replace_fields(item, r"\bمریخ\b", "مارس")
    if "juice it up" in source:
        changed += _replace_fields(item, r"آب\s+(?:آن|این)\s+را\s+بالا[!！]?", "جوس ایت آپ")
    if "gen z" in source:
        changed += _replace_fields(item, r"(?:جنرال|ژنرال)\s*[Zzزد]", "نسل زد")
    if "footprint" in str(item.get("title") or "").lower():
        changed += _replace_fields(item, r"\bردپا(?:ی خود)?\b", "حضور")
    if re.search(r"\btaps\b", str(item.get("title") or ""), re.I):
        changed += _replace_fields(item, r"\bمی(?:‌| )زند\b", "انتخاب می‌کند")
    if "beverage alcohol reset" in source:
        changed += _replace_fields(item, r"تنظیم مجدد الکل نوشیدنی", "تغییرات بازار نوشیدنی‌های الکلی")

    return changed


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    translator = PersianTranslator(timeout=5, pause=0.05)

    deterministic_repairs = 0
    for item in items:
        deterministic_repairs += direct_semantic_repairs(item)
        item["translation_quality"] = combined_quality(item)

    candidates = [
        item for item in items
        if needs_repair(item)
        and item.get("language") != "fa"
        and not looks_persian(item.get("title", ""))
        and item.get("title_fa")
    ]
    candidates.sort(
        key=lambda x: (
            0 if set((x.get("translation_quality") or {}).get("issues") or []) & SEMANTIC_REPAIR_ISSUES else 1,
            -(x.get("relevance_score") or 0),
        )
    )

    retried = fixed = failed = 0
    for item in candidates[:80]:
        before = set((item.get("translation_quality") or {}).get("issues") or []) & SEMANTIC_REPAIR_ISSUES
        try:
            if retry_item(item, translator):
                retried += 1
                deterministic_repairs += direct_semantic_repairs(item)
                item["translation_quality"] = combined_quality(item)
                after = set(item["translation_quality"].get("issues") or []) & SEMANTIC_REPAIR_ISSUES
                if before and not after:
                    fixed += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    quarantined = 0
    counts = {"pass": 0, "warn": 0, "retry": 0, "block": 0}
    issues: dict[str, int] = {}
    for item in items:
        direct_semantic_repairs(item)
        item["translation_quality"] = combined_quality(item)
        q = item["translation_quality"]
        counts[q["status"]] = counts.get(q["status"], 0) + 1
        for issue in q.get("issues", []) or []:
            issues[issue] = issues.get(issue, 0) + 1
        if not q.get("publishable", False) and item.get("language") != "fa" and item.get("title_fa"):
            _quarantine(item)
            quarantined += 1

    stats = {
        **counts,
        "total": len(items),
        "publishable": counts.get("pass", 0) + counts.get("warn", 0),
        "semantic_candidates": len(candidates),
        "semantic_retried": retried,
        "semantic_fixed": fixed,
        "deterministic_repairs": deterministic_repairs,
        "semantic_retry_failed": failed,
        "semantic_quarantined": quarantined,
        "top_issues": dict(sorted(issues.items(), key=lambda x: (-x[1], x[0]))[:12]),
    }
    payload["schema_version"] = "0.18.1"
    payload["translation_quality_stats"] = stats
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Semantic repair: {len(candidates)} candidates; {retried} retried; {fixed} fixed; "
        f"{deterministic_repairs} direct repairs; {failed} failed; {quarantined} quarantined."
    )


if __name__ == "__main__":
    main()
