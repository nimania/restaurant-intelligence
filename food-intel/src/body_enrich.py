from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from body_reader import enrich_article_bodies
from translate_fa import PersianTranslator, compact_words, looks_persian

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "news.json"
MAX_REPORT_WORDS = 210
MAX_CHUNKS = 3
CHUNK_CHARS = 900


def _chunks(text: str) -> list[str]:
    sentences = [x.strip() for x in re.split(r"(?<=[.!?؟!])\s+", text or "") if x.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= CHUNK_CHARS:
            current = f"{current} {sentence}".strip()
            continue
        if current:
            chunks.append(current)
        current = sentence
        if len(chunks) >= MAX_CHUNKS:
            break
    if current and len(chunks) < MAX_CHUNKS:
        chunks.append(current)
    return chunks[:MAX_CHUNKS]


def translate_report(translator: PersianTranslator, source: str) -> str:
    translated: list[str] = []
    for chunk in _chunks(source):
        translated.append(translator.translate(chunk, CHUNK_CHARS))
    return compact_words(" ".join(translated), MAX_REPORT_WORDS)


def _previous_snapshot(items: list[dict]) -> dict[str, dict]:
    """Build a reusable cache view even when the collector refreshed an RSS item.

    collect.py preserves report_fa/report_coverage on refreshed feed entries but older
    body-reader metadata may be absent. A report explicitly marked as body-based is
    therefore sufficient evidence to avoid downloading the same article again.
    """
    result: dict[str, dict] = {}
    for item in items:
        item_id = item.get("id")
        if not item_id:
            continue
        previous = copy.deepcopy(item)
        if previous.get("report_fa") and previous.get("report_coverage") == "بر پایه بدنه مقاله":
            previous.setdefault("article_body", {"status": "extracted", "cached_from_report": True})
            previous["report_source_kind"] = "article_body"
        result[item_id] = previous
    return result


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit("news.json does not exist")

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    previous_by_id = _previous_snapshot(items)

    stats = enrich_article_bodies(items, previous_by_id)
    translator = PersianTranslator(timeout=5, pause=0.06)
    report_upgraded = 0
    report_failed = 0

    for item in items:
        source = item.pop("_report_source", "")
        if not source or item.get("report_source_kind") != "article_body":
            continue

        # Persian publisher text is not republished as an extract. Until an abstractive
        # summarizer is available, keep the existing publisher-supplied Persian summary.
        if item.get("language") == "fa" or looks_persian(item.get("title", "")):
            item["report_basis"] = "feed-summary"
            continue

        try:
            report = translate_report(translator, source)
            if report:
                item["report_fa"] = report
                if not item.get("summary_fa"):
                    item["summary_fa"] = compact_words(report, 85)
                item["report_coverage"] = "بر پایه بدنه مقاله"
                item["report_basis"] = "article-body-summary"
                item["report_word_count"] = len(report.split())
                report_upgraded += 1
        except Exception as exc:
            item["body_report_error"] = str(exc)[:140]
            report_failed += 1

    payload["schema_version"] = "0.10.1"
    payload["article_body_stats"] = {
        "attempted": stats.attempted,
        "extracted": stats.extracted,
        "blocked": stats.blocked,
        "short": stats.short,
        "failed": stats.failed,
        "reused": stats.reused,
        "queued": stats.queued,
        "reports_upgraded": report_upgraded,
        "report_translation_failed": report_failed,
    }
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "Article body reader: "
        f"{stats.attempted} attempted; {stats.extracted} extracted; {stats.blocked} blocked; "
        f"{stats.short} short; {stats.failed} failed; {stats.reused} reused; {stats.queued} queued."
    )
    print(f"Body-based Persian reports: {report_upgraded} upgraded; {report_failed} translation failures.")


if __name__ == "__main__":
    main()
