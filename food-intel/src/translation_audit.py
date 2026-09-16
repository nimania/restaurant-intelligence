from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "news.json"
SAMPLE_LIMIT = 12


def clean(value: object, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def quality(item: dict) -> str:
    q = item.get("translation_quality") or {}
    issues = q.get("issues") or []
    return f"{q.get('status') or '—'}" + (f" | {', '.join(map(str, issues[:4]))}" if issues else "")


def eligible(item: dict) -> bool:
    if not item.get("title_fa") or item.get("language") == "fa":
        return False
    if int(item.get("narrative_version") or 0) >= 2:
        return True
    return int((item.get("translation") or {}).get("cleanup_version") or 0) >= 2


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit("news.json does not exist")
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    rows = [x for x in payload.get("items", []) if eligible(x)]
    rows.sort(
        key=lambda x: (
            int(x.get("narrative_version") or 0) >= 2,
            x.get("published_at") or "",
            x.get("relevance_score") or 0,
        ),
        reverse=True,
    )

    print("\n=== Persian v2 human audit samples ===")
    if not rows:
        print("No publishable v2 samples yet.")
        return

    for index, item in enumerate(rows[:SAMPLE_LIMIT], 1):
        brands = ", ".join((b.get("name") or b.get("fa") or b.get("id") or "") for b in (item.get("brands") or [])[:3])
        print(f"\n--- SAMPLE {index} ---")
        print(f"ID: {item.get('id', '')}")
        print(f"Source: {(item.get('source') or {}).get('name', '')} | Brands: {brands or '—'}")
        print(f"Quality: {quality(item)} | narrative_v={item.get('narrative_version') or 0}")
        print(f"EN title: {clean(item.get('title'), 240)}")
        print(f"FA title: {clean(item.get('title_fa'), 260)}")
        print(f"30s recap: {clean(item.get('recap_fa') or item.get('summary_fa'), 700)}")
        print(f"FA report: {clean(item.get('narrative_fa') or item.get('report_fa'), 1200)}")

    print("\n=== End Persian v2 audit ===")


if __name__ == "__main__":
    main()
