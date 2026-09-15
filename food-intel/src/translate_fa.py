from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fa_editor import editorial_meta, editorialize_report, editorialize_summary, editorialize_title
from fa_polish import polish_persian, prepare_for_translation

PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")
DEFAULT_TRANSLATION_LIMIT = 180
MAX_CONSECUTIVE_FAILURES = 4
GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
MYMEMORY_ENDPOINT = "https://api.mymemory.translated.net/get"
SPLIT_MARKER = "[[[NIMA_SPLIT_9F7C]]]"
CLEANUP_VERSION = 1

DEEP_ENRICHMENT_FIELDS = (
    "narrative_fa",
    "narrative_basis",
    "narrative_version",
    "narrative_word_count",
    "article_body",
    "report_source_kind",
    "report_source_chars",
    "report_selected_chars",
    "report_basis",
    "report_word_count",
    "key_points_fa",
)


def looks_persian(text: str) -> bool:
    if not text:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    fa_letters = len(PERSIAN_RE.findall(text))
    return fa_letters / max(len(letters), 1) >= 0.30


def compact(text: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", (text or "")).strip()
    if len(value) <= limit:
        return value
    return value[:limit].rsplit(" ", 1)[0].rstrip("،؛,:-. ") + "…"


def compact_words(text: str, max_words: int = 190) -> str:
    value = re.sub(r"\s+", " ", (text or "")).strip()
    words = value.split()
    if len(words) <= max_words:
        return value
    return " ".join(words[:max_words]).rstrip("،؛,:-. ") + "…"


def coverage_label(source_chars: int | None) -> str:
    n = int(source_chars or 0)
    if n >= 1200:
        return "گسترده"
    if n >= 500:
        return "متوسط"
    return "خلاصه منبع"


def restore_deep_enrichment(item: dict, previous: dict) -> None:
    """Keep body/narrative enrichment when an unchanged feed item is refreshed."""
    for field in DEEP_ENRICHMENT_FIELDS:
        if previous.get(field) is not None:
            item[field] = previous.get(field)


@dataclass
class TranslationStats:
    translated: int = 0
    reused: int = 0
    persian_original: int = 0
    failed: int = 0
    queued: int = 0


class PersianTranslator:
    """Lightweight HTTP English→Persian translator with editorial cleanup."""

    def __init__(self, timeout: int = 4, pause: float = 0.08) -> None:
        self.timeout = timeout
        self.pause = pause

    def _read_json(self, url: str) -> object:
        request = Request(
            url,
            headers={
                "User-Agent": "FoodIndustryIntelligence/1.2 (+https://github.com/nimania/restaurant-intelligence)",
                "Accept": "application/json,text/plain,*/*",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _google(self, text: str) -> str:
        query = urlencode({
            "client": "gtx",
            "sl": "auto",
            "tl": "fa",
            "dt": "t",
            "q": text,
        })
        payload = self._read_json(f"{GOOGLE_ENDPOINT}?{query}")
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
            raise RuntimeError("unexpected primary translation response")
        translated = "".join(
            part[0] for part in payload[0]
            if isinstance(part, list) and part and isinstance(part[0], str)
        ).strip()
        if not translated:
            raise RuntimeError("empty primary translation response")
        return translated

    def _mymemory(self, text: str) -> str:
        if len(text.encode("utf-8")) > 450:
            raise RuntimeError("fallback text is too long")
        query = urlencode({"q": text, "langpair": "en|fa"})
        payload = self._read_json(f"{MYMEMORY_ENDPOINT}?{query}")
        translated = ""
        if isinstance(payload, dict):
            translated = str((payload.get("responseData") or {}).get("translatedText") or "").strip()
        if not translated:
            raise RuntimeError("empty fallback translation response")
        return translated

    def translate(self, text: str, limit: int) -> str:
        text = compact(prepare_for_translation(text), limit)
        if not text:
            return ""
        if looks_persian(text) and not re.search(r"[A-Za-z]{4,}", text):
            return compact(polish_persian(text), limit + 220)

        last_error: Exception | None = None
        for engine in (self._google, self._mymemory):
            try:
                translated = polish_persian(engine(text))
                if translated and looks_persian(translated):
                    time.sleep(self.pause)
                    return compact(translated, limit + 220)
                last_error = RuntimeError("translation result is not Persian")
            except Exception as exc:
                last_error = exc
        raise RuntimeError(str(last_error or "translation failed"))

    def translate_article(self, title: str, summary: str, report_source: str = "") -> tuple[str, str, str]:
        title = compact(title, 240)
        summary = compact(summary, 520)
        body = compact(report_source or summary, 1200)

        if body:
            combined = f"{title}\n\n{SPLIT_MARKER}\n\n{body}"
            try:
                translated = self.translate(combined, 1550)
                if SPLIT_MARKER in translated:
                    title_fa, body_fa = translated.split(SPLIT_MARKER, 1)
                    title_fa = editorialize_title(compact(polish_persian(title_fa), 420))
                    body_raw = compact_words(polish_persian(body_fa), 190)
                    body_fa = editorialize_report(body_raw)
                    if title_fa and looks_persian(title_fa) and body_fa:
                        summary_fa = compact_words(editorialize_summary(body_raw, 3), 85)
                        return title_fa, summary_fa, body_fa
            except Exception:
                pass

        if not summary:
            title_fa = editorialize_title(self.translate(title, 240))
            return title_fa, "", ""

        combined = f"{title}\n\n{SPLIT_MARKER}\n\n{summary}"
        try:
            translated = self.translate(combined, 820)
            if SPLIT_MARKER in translated:
                title_fa, summary_fa = translated.split(SPLIT_MARKER, 1)
                title_fa = editorialize_title(compact(polish_persian(title_fa), 420))
                summary_raw = compact_words(polish_persian(summary_fa), 85)
                summary_fa = editorialize_summary(summary_raw, 3)
                if title_fa and looks_persian(title_fa):
                    return title_fa, summary_fa, editorialize_report(summary_raw)
        except Exception:
            pass

        title_fa = editorialize_title(self.translate(title, 240))
        summary_raw = compact_words(self.translate(summary, 520), 85)
        summary_fa = editorialize_summary(summary_raw, 3)
        return title_fa, summary_fa, editorialize_report(summary_raw)


def _translation_limit() -> int:
    try:
        return max(0, int(os.getenv("FOOD_INTEL_TRANSLATION_LIMIT", DEFAULT_TRANSLATION_LIMIT)))
    except (TypeError, ValueError):
        return DEFAULT_TRANSLATION_LIMIT


def _meta(status: str, engine: str | None) -> dict:
    return {"status": status, "engine": engine, "cleanup_version": CLEANUP_VERSION}


def apply_persian_translation(
    items: list[dict], previous_by_id: dict[str, dict] | None = None
) -> TranslationStats:
    previous_by_id = previous_by_id or {}
    stats = TranslationStats()
    translator = PersianTranslator()
    pending: list[dict] = []

    for item in items:
        title = item.get("title", "")
        summary = item.get("summary", "")
        previous = previous_by_id.get(item.get("id", ""), {})
        source_chars = item.get("source_detail_chars") or len(summary)

        if item.get("language") == "fa" or looks_persian(title):
            item["title_fa"] = polish_persian(title)
            item["summary_fa"] = compact(polish_persian(summary), 520)
            item["report_fa"] = compact_words(polish_persian(summary), 150)
            item["report_coverage"] = "خلاصه منبع"
            item["translation"] = _meta("original-fa", None)
            item["editorial"] = editorial_meta("source-fa-normalized")
            stats.persian_original += 1
            continue

        same_source_text = (
            previous.get("title") == title
            and previous.get("summary") == summary
            and previous.get("title_fa")
        )
        if same_source_text:
            restore_deep_enrichment(item, previous)

        if same_source_text and previous.get("report_fa"):
            item["title_fa"] = editorialize_title(previous.get("title_fa", ""))
            item["summary_fa"] = editorialize_summary(previous.get("summary_fa", ""), 3)
            # If a body-based narrative exists it is the canonical public report.
            canonical_report = previous.get("narrative_fa") or previous.get("report_fa", previous.get("summary_fa", ""))
            item["report_fa"] = editorialize_report(canonical_report)
            if previous.get("narrative_fa"):
                item["narrative_fa"] = item["report_fa"]
            item["report_coverage"] = previous.get("report_coverage") or coverage_label(source_chars)
            item["translation"] = _meta(
                "translated",
                (previous.get("translation") or {}).get("engine") or "http-en-fa",
            )
            item["editorial"] = editorial_meta("edited-cache")
            stats.reused += 1
            continue

        if same_source_text:
            item["title_fa"] = editorialize_title(previous.get("title_fa", ""))
            item["summary_fa"] = editorialize_summary(previous.get("summary_fa", ""), 3)
            item["report_fa"] = editorialize_report(previous.get("report_fa", ""))
        else:
            item["title_fa"] = ""
            item["summary_fa"] = ""
            item["report_fa"] = ""
            item.pop("narrative_fa", None)
        item["report_coverage"] = coverage_label(source_chars)
        item["translation"] = _meta("queued", "http-en-fa")
        item["editorial"] = editorial_meta("pending")
        pending.append(item)

    pending.sort(
        key=lambda x: (x.get("relevance_score") or 0, x.get("published_at") or ""),
        reverse=True,
    )
    limit = _translation_limit()
    consecutive_failures = 0

    for index, item in enumerate(pending):
        if index >= limit:
            stats.queued += 1
            continue

        try:
            title_fa, summary_fa, report_fa = translator.translate_article(
                item.get("title", ""),
                item.get("summary", ""),
                item.get("_report_source", ""),
            )
            item["title_fa"] = editorialize_title(title_fa or item.get("title_fa", ""))
            item["summary_fa"] = editorialize_summary(summary_fa or item.get("summary_fa", ""), 3)
            item["report_fa"] = editorialize_report(report_fa or item.get("summary_fa", ""))
            item["report_coverage"] = coverage_label(item.get("source_detail_chars"))
            item["translation"] = _meta("translated", "http-en-fa")
            item["editorial"] = editorial_meta("edited")
            stats.translated += 1
            consecutive_failures = 0
        except Exception as exc:
            item["translation"] = {
                **_meta("failed", "http-en-fa"),
                "error": str(exc)[:160],
            }
            item["editorial"] = editorial_meta("pending")
            stats.failed += 1
            consecutive_failures += 1

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                remaining = min(limit, len(pending)) - index - 1
                if remaining > 0:
                    stats.queued += remaining
                if len(pending) > limit:
                    stats.queued += len(pending) - limit
                break

    return stats
