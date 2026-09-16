from __future__ import annotations

import copy
import json
from pathlib import Path

from body_reader import enrich_article_bodies
from fa_editor import editorial_meta
from fa_narrative import build_narrative, source_chunks
from translate_fa import PersianTranslator, compact_words, looks_persian

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "news.json"
NARRATIVE_VERSION = 2


def translate_narrative(translator: PersianTranslator, source: str, title_fa: str = "") -> tuple[str, str]:
    """Translate short factual source units independently, then create Persian recap/report."""
    translated: list[str] = []
    for unit in source_chunks(source):
        translated.append(translator.translate(unit, 340))
    return build_narrative(translated, title_fa=title_fa)


def _previous_snapshot(items: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in items:
        item_id = item.get("id")
        if not item_id:
            continue
        previous = copy.deepcopy(item)
        if (
            previous.get("narrative_fa")
            and previous.get("report_coverage") == "بر پایه بدنه مقاله"
            and int(previous.get("narrative_version") or 0) >= NARRATIVE_VERSION
        ):
            previous.setdefault("article_body", {"status": "extracted", "cached_from_narrative": True})
            previous["report_source_kind"] = "article_body"
        else:
            # Force v1/legacy reports back through the source reader so public prose
            # is gradually replaced by sentence-level v2 recaps.
            previous.pop("article_body", None)
            previous.pop("report_source_kind", None)
            previous.pop("report_source_chars", None)
            previous.pop("report_selected_chars", None)
        result[item_id] = previous
    return result


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit("news.json does not exist")

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    previous_by_id = _previous_snapshot(items)

    stats = enrich_article_bodies(items, previous_by_id)
    translator = PersianTranslator(timeout=5, pause=0.04)
    upgraded = 0
    failed = 0

    for item in items:
        source = item.pop("_report_source", "")
        if not source or item.get("report_source_kind") != "article_body":
            continue

        if item.get("language") == "fa" or looks_persian(item.get("title", "")):
            item["report_basis"] = "feed-summary"
            item["editorial"] = editorial_meta("source-fa-normalized")
            continue

        try:
            report, recap = translate_narrative(translator, source, title_fa=str(item.get("title_fa") or ""))
            if report:
                item["narrative_fa"] = report
                item["recap_fa"] = recap or compact_words(report, 105)
                item["report_fa"] = report
                item["summary_fa"] = item["recap_fa"]
                item["report_coverage"] = "بر پایه بدنه مقاله"
                item["report_basis"] = "source-sentence-recap"
                item["narrative_basis"] = "sentence-level source translation, public recap reconstruction"
                item["narrative_version"] = NARRATIVE_VERSION
                item["narrative_word_count"] = len(report.replace("\n", " ").split())
                item["report_word_count"] = item["narrative_word_count"]
                item["editorial"] = editorial_meta("source-recap-v2")
                upgraded += 1
        except Exception as exc:
            item["narrative_error"] = str(exc)[:160]
            failed += 1

    payload["schema_version"] = "0.22"
    payload["article_body_stats"] = {
        "attempted": stats.attempted,
        "extracted": stats.extracted,
        "blocked": stats.blocked,
        "short": stats.short,
        "failed": stats.failed,
        "reused": stats.reused,
        "queued": stats.queued,
        "recaps_upgraded": upgraded,
        "recap_translation_failed": failed,
        "narrative_version": NARRATIVE_VERSION,
    }
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "Article body reader: "
        f"{stats.attempted} attempted; {stats.extracted} extracted; {stats.blocked} blocked; "
        f"{stats.short} short; {stats.failed} failed; {stats.reused} reused; {stats.queued} queued."
    )
    print(f"Persian source recaps v2: {upgraded} upgraded; {failed} translation failures.")


if __name__ == "__main__":
    main()
