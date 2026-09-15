from __future__ import annotations

import json
import os
import re
from pathlib import Path

from fa_editor import editorial_meta, editorialize_report, editorialize_summary, editorialize_title
from fa_polish import polish_persian
from translate_fa import PersianTranslator, compact_words, looks_persian
from translation_quality import assess_item, quality_stats

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "news.json"
DEFAULT_RETRY_LIMIT = 60
SOURCE_CHUNK_CHARS = 320


def _retry_limit() -> int:
    try:
        return max(0, int(os.getenv("FOOD_INTEL_QUALITY_RETRY_LIMIT", DEFAULT_RETRY_LIMIT)))
    except (TypeError, ValueError):
        return DEFAULT_RETRY_LIMIT


def _source_chunks(text: str) -> list[str]:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return []
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", value) if x.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= SOURCE_CHUNK_CHARS:
            current = f"{current} {sentence}".strip()
            continue
        if current:
            chunks.append(current)
        current = sentence
    if current:
        chunks.append(current)
    return chunks or [value[:SOURCE_CHUNK_CHARS]]


def _translate_source(translator: PersianTranslator, source: str, max_chunks: int = 4) -> str:
    parts: list[str] = []
    for chunk in _source_chunks(source)[:max_chunks]:
        parts.append(translator.translate(chunk, SOURCE_CHUNK_CHARS))
    return polish_persian(" ".join(x for x in parts if x))


def retry_item(item: dict, translator: PersianTranslator) -> bool:
    title = str(item.get("title") or "").strip()
    summary = str(item.get("summary") or "").strip()
    if not title:
        return False

    title_fa = editorialize_title(translator.translate(title, 260))
    summary_fa = ""
    if summary:
        translated_summary = _translate_source(translator, summary, max_chunks=3)
        summary_fa = compact_words(editorialize_summary(translated_summary, 3), 90)

    existing_narrative = str(item.get("narrative_fa") or "").strip()
    existing_report = str(item.get("report_fa") or "").strip()
    narrative_fa = editorialize_report(existing_narrative) if existing_narrative else ""
    report_fa = narrative_fa or (editorialize_report(existing_report) if existing_report else "")
    if not report_fa and summary_fa:
        report_fa = editorialize_report(summary_fa)

    item["title_fa"] = title_fa
    item["summary_fa"] = summary_fa
    item["report_fa"] = report_fa
    if narrative_fa:
        item["narrative_fa"] = narrative_fa
    item["translation"] = {
        **(item.get("translation") or {}),
        "status": "translated",
        "engine": "http-en-fa",
        "quality_retry": True,
    }
    item["editorial"] = editorial_meta("quality-retry")
    return bool(title_fa and summary_fa)


def _quarantine(item: dict) -> None:
    """Hide bad public Persian without deleting the failed attempt."""
    quality = item.get("translation_quality") or {}
    item["translation_quarantine"] = {
        "title_fa": item.get("title_fa", ""),
        "summary_fa": item.get("summary_fa", ""),
        "report_fa": item.get("report_fa", ""),
        "narrative_fa": item.get("narrative_fa", ""),
        "quality": quality,
    }
    item["title_fa"] = ""
    item["summary_fa"] = ""
    item["report_fa"] = ""
    item["narrative_fa"] = ""
    item["translation"] = {
        **(item.get("translation") or {}),
        "status": "quality-quarantined",
    }


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit("news.json does not exist")

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    translator = PersianTranslator(timeout=5, pause=0.05)

    for item in items:
        item["translation_quality"] = assess_item(item)

    candidates = [
        item for item in items
        if item.get("translation_quality", {}).get("status") in {"retry", "block"}
        and item.get("language") != "fa"
        and not looks_persian(item.get("title", ""))
    ]
    candidates.sort(
        key=lambda x: (
            0 if x.get("translation_quality", {}).get("status") == "block" else 1,
            -(x.get("relevance_score") or 0),
            x.get("published_at") or "",
        )
    )

    retried = 0
    improved = 0
    retry_failed = 0
    for item in candidates[:_retry_limit()]:
        before = int(item.get("translation_quality", {}).get("score") or 0)
        try:
            if retry_item(item, translator):
                retried += 1
                item["translation_quality"] = assess_item(item)
                after = int(item["translation_quality"].get("score") or 0)
                if after > before:
                    improved += 1
            else:
                retry_failed += 1
        except Exception as exc:
            item["quality_retry_error"] = str(exc)[:160]
            retry_failed += 1

    for item in items:
        item["translation_quality"] = assess_item(item)

    stats = quality_stats(items)
    quarantined = 0
    for item in items:
        quality = item.get("translation_quality") or {}
        if not quality.get("publishable", False) and item.get("language") != "fa":
            _quarantine(item)
            quarantined += 1

    stats.update({
        "retry_candidates": len(candidates),
        "retried": retried,
        "improved": improved,
        "retry_failed": retry_failed,
        "quarantined": quarantined,
    })
    payload["schema_version"] = "0.17"
    payload["translation_quality_stats"] = stats
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "Translation quality: "
        f"{stats.get('pass', 0)} pass; {stats.get('warn', 0)} warn; "
        f"{stats.get('retry', 0)} retry; {stats.get('block', 0)} block; "
        f"{retried} retried; {improved} improved; {retry_failed} retry failures; "
        f"{quarantined} quarantined from public feed."
    )


if __name__ == "__main__":
    main()
