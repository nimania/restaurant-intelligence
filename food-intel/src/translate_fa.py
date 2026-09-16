from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fa_editor import editorial_meta, editorialize_report, editorialize_summary, editorialize_title
from fa_polish import (
    EXTRA_BRAND_TERMS,
    TERM_GLOSSARY,
    brand_replacements,
    normalize_source_semantics,
    polish_persian,
)

PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")
DEFAULT_TRANSLATION_LIMIT = 180
MAX_CONSECUTIVE_FAILURES = 4
GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
MYMEMORY_ENDPOINT = "https://api.mymemory.translated.net/get"
SPLIT_MARKER = "[[[NIMA_SPLIT_9F7C]]]"
CLEANUP_VERSION = 2

DEEP_ENRICHMENT_FIELDS = (
    "narrative_fa", "recap_fa", "narrative_basis", "narrative_version",
    "narrative_word_count", "article_body", "report_source_kind",
    "report_source_chars", "report_selected_chars", "report_basis",
    "report_word_count", "key_points_fa",
)


def looks_persian(text: str) -> bool:
    if not text:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return len(PERSIAN_RE.findall(text)) / max(len(letters), 1) >= 0.30


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
    return "گسترده" if n >= 1200 else "متوسط" if n >= 500 else "خلاصه منبع"


def restore_deep_enrichment(item: dict, previous: dict) -> None:
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


def _ascii_replace(text: str, source: str, replacement: str) -> str:
    pattern = rf"(?<![A-Za-z0-9]){re.escape(source)}(?![A-Za-z0-9])"
    return re.sub(pattern, replacement, text, flags=re.IGNORECASE)


def _protect_source_terms(text: str) -> tuple[str, dict[str, str]]:
    """Protect brands/industry terminology without mixing Persian into English input.

    Previous versions inserted Persian words into the English source before sending it
    to the translator. That mixed-language input was a major source of broken syntax.
    v2 keeps input English and uses opaque ASCII placeholders, restored afterwards.
    """
    value = normalize_source_semantics(text)
    replacements: list[tuple[str, str]] = []
    replacements.extend(brand_replacements())
    replacements.extend(EXTRA_BRAND_TERMS)
    replacements.extend(TERM_GLOSSARY)
    seen: set[str] = set()
    ordered: list[tuple[str, str]] = []
    for source, target in sorted(replacements, key=lambda x: len(x[0]), reverse=True):
        key = source.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append((source, target))
    protected: dict[str, str] = {}
    for i, (source, target) in enumerate(ordered):
        token = f"NIMATERM{i:04d}ZXQ"
        new_value = _ascii_replace(value, source, token)
        if new_value != value:
            protected[token] = target
            value = new_value
    return value, protected


def _restore_source_terms(text: str, protected: dict[str, str]) -> str:
    value = text
    for token, target in protected.items():
        value = re.sub(re.escape(token), target, value, flags=re.IGNORECASE)
        # Some engines may insert a space before the suffix.
        value = re.sub(re.escape(token.replace("ZXQ", " ZXQ")), target, value, flags=re.IGNORECASE)
    return value


class PersianTranslator:
    def __init__(self, timeout: int = 4, pause: float = 0.06) -> None:
        self.timeout = timeout
        self.pause = pause

    def _read_json(self, url: str) -> object:
        request = Request(url, headers={
            "User-Agent": "FoodIndustryIntelligence/2.0 (+https://github.com/nimania/restaurant-intelligence)",
            "Accept": "application/json,text/plain,*/*",
        })
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _google(self, text: str) -> str:
        query = urlencode({"client": "gtx", "sl": "en", "tl": "fa", "dt": "t", "q": text})
        payload = self._read_json(f"{GOOGLE_ENDPOINT}?{query}")
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
            raise RuntimeError("unexpected primary translation response")
        translated = "".join(part[0] for part in payload[0] if isinstance(part, list) and part and isinstance(part[0], str)).strip()
        if not translated:
            raise RuntimeError("empty primary translation response")
        return translated

    def _mymemory(self, text: str) -> str:
        if len(text.encode("utf-8")) > 450:
            raise RuntimeError("fallback text is too long")
        payload = self._read_json(f"{MYMEMORY_ENDPOINT}?{urlencode({'q': text, 'langpair': 'en|fa'})}")
        translated = str((payload.get("responseData") or {}).get("translatedText") or "").strip() if isinstance(payload, dict) else ""
        if not translated:
            raise RuntimeError("empty fallback translation response")
        return translated

    def translate(self, text: str, limit: int) -> str:
        source = compact(text, limit)
        if not source:
            return ""
        if looks_persian(source) and not re.search(r"[A-Za-z]{4,}", source):
            return compact(polish_persian(source), limit + 220)
        protected_source, protected = _protect_source_terms(source)
        last_error: Exception | None = None
        for engine in (self._google, self._mymemory):
            try:
                translated = _restore_source_terms(engine(protected_source), protected)
                translated = polish_persian(translated)
                if translated and looks_persian(translated):
                    time.sleep(self.pause)
                    return compact(translated, limit + 260)
                last_error = RuntimeError("translation result is not Persian")
            except Exception as exc:
                last_error = exc
        raise RuntimeError(str(last_error or "translation failed"))

    def translate_article(self, title: str, summary: str, report_source: str = "") -> tuple[str, str, str]:
        title = compact(title, 240)
        summary = compact(summary, 520)
        body = compact(report_source or summary, 1200)
        title_fa = editorialize_title(self.translate(title, 240))
        source_for_public = body or summary
        if not source_for_public:
            return title_fa, "", ""
        # Short feed-level fallback only. Full body-based reporting is handled later
        # sentence-by-sentence in body_enrich.py.
        translated = self.translate(source_for_public, min(max(len(source_for_public) + 80, 520), 1280))
        summary_fa = editorialize_summary(compact_words(translated, 80), 3)
        report_fa = editorialize_report(compact_words(translated, 150))
        return title_fa, summary_fa, report_fa


def _translation_limit() -> int:
    try:
        return max(0, int(os.getenv("FOOD_INTEL_TRANSLATION_LIMIT", DEFAULT_TRANSLATION_LIMIT)))
    except (TypeError, ValueError):
        return DEFAULT_TRANSLATION_LIMIT


def _meta(status: str, engine: str | None) -> dict:
    return {"status": status, "engine": engine, "cleanup_version": CLEANUP_VERSION}


def apply_persian_translation(items: list[dict], previous_by_id: dict[str, dict] | None = None) -> TranslationStats:
    previous_by_id = previous_by_id or {}
    stats = TranslationStats()
    translator = PersianTranslator()
    pending: list[dict] = []

    for item in items:
        title, summary = item.get("title", ""), item.get("summary", "")
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

        same_source = previous.get("title") == title and previous.get("summary") == summary and previous.get("title_fa")
        previous_version = int((previous.get("translation") or {}).get("cleanup_version") or 0)
        if same_source:
            restore_deep_enrichment(item, previous)

        # v2 invalidates old feed-level translations so broken mixed-language cache is replaced.
        if same_source and previous_version >= CLEANUP_VERSION and previous.get("report_fa"):
            item["title_fa"] = editorialize_title(previous.get("title_fa", ""))
            item["summary_fa"] = editorialize_summary(previous.get("summary_fa", ""), 3)
            canonical = previous.get("narrative_fa") or previous.get("report_fa", "")
            item["report_fa"] = editorialize_report(canonical)
            if previous.get("narrative_fa"):
                item["narrative_fa"] = item["report_fa"]
            item["report_coverage"] = previous.get("report_coverage") or coverage_label(source_chars)
            item["translation"] = _meta("translated", (previous.get("translation") or {}).get("engine") or "http-en-fa-v2")
            item["editorial"] = editorial_meta("edited-cache-v2")
            stats.reused += 1
            continue

        item["title_fa"] = ""
        item["summary_fa"] = ""
        item["report_fa"] = ""
        if not previous.get("narrative_fa"):
            item.pop("narrative_fa", None)
        item["report_coverage"] = coverage_label(source_chars)
        item["translation"] = _meta("queued", "http-en-fa-v2")
        item["editorial"] = editorial_meta("pending-v2")
        pending.append(item)

    pending.sort(key=lambda x: (x.get("relevance_score") or 0, x.get("published_at") or ""), reverse=True)
    limit = _translation_limit()
    consecutive_failures = 0
    for index, item in enumerate(pending):
        if index >= limit:
            stats.queued += 1
            continue
        try:
            title_fa, summary_fa, report_fa = translator.translate_article(item.get("title", ""), item.get("summary", ""), item.get("_report_source", ""))
            item["title_fa"] = editorialize_title(title_fa)
            item["summary_fa"] = editorialize_summary(summary_fa, 3)
            item["report_fa"] = editorialize_report(report_fa or summary_fa)
            item["report_coverage"] = coverage_label(item.get("source_detail_chars"))
            item["translation"] = _meta("translated", "http-en-fa-v2")
            item["editorial"] = editorial_meta("edited-v2")
            stats.translated += 1
            consecutive_failures = 0
        except Exception as exc:
            item["translation"] = {**_meta("failed", "http-en-fa-v2"), "error": str(exc)[:160]}
            item["editorial"] = editorial_meta("pending-v2")
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
