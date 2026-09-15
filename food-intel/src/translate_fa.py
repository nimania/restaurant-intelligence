from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fa_polish import polish_persian, prepare_for_translation

PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")
DEFAULT_TRANSLATION_LIMIT = 180
MAX_CONSECUTIVE_FAILURES = 4
GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
MYMEMORY_ENDPOINT = "https://api.mymemory.translated.net/get"
SPLIT_MARKER = "[[[NIMA_SPLIT_9F7C]]]"
CLEANUP_VERSION = 1


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


@dataclass
class TranslationStats:
    translated: int = 0
    reused: int = 0
    persian_original: int = 0
    failed: int = 0
    queued: int = 0


class PersianTranslator:
    """Lightweight HTTP English→Persian translator with terminology cleanup.

    Successful translations are persisted in news.json and reused. Translation is a
    best-effort enrichment: network/rate-limit problems never block news collection.
    A restaurant-industry glossary and brand-name normalization are applied before
    and after translation so mixed Persian/English output stays readable.
    """

    def __init__(self, timeout: int = 4, pause: float = 0.08) -> None:
        self.timeout = timeout
        self.pause = pause

    def _read_json(self, url: str) -> object:
        request = Request(
            url,
            headers={
                "User-Agent": "FoodIndustryIntelligence/1.1 (+https://github.com/nimania/restaurant-intelligence)",
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
                    title_fa = compact(polish_persian(title_fa), 420).strip()
                    body_fa = compact_words(polish_persian(body_fa), 190).strip()
                    if title_fa and looks_persian(title_fa) and body_fa:
                        summary_fa = compact_words(body_fa, 85)
                        return title_fa, summary_fa, body_fa
            except Exception:
                pass

        if not summary:
            title_fa = self.translate(title, 240)
            return title_fa, "", ""

        combined = f"{title}\n\n{SPLIT_MARKER}\n\n{summary}"
        try:
            translated = self.translate(combined, 820)
            if SPLIT_MARKER in translated:
                title_fa, summary_fa = translated.split(SPLIT_MARKER, 1)
                title_fa = compact(polish_persian(title_fa), 420).strip()
                summary_fa = compact_words(polish_persian(summary_fa), 85).strip()
                if title_fa and looks_persian(title_fa):
                    return title_fa, summary_fa, summary_fa
        except Exception:
            pass

        title_fa = self.translate(title, 240)
        summary_fa = compact_words(self.translate(summary, 520), 85)
        return polish_persian(title_fa), polish_persian(summary_fa), polish_persian(summary_fa)


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
            stats.persian_original += 1
            continue

        same_source_text = (
            previous.get("title") == title
            and previous.get("summary") == summary
            and previous.get("title_fa")
        )
        if same_source_text and previous.get("report_fa"):
            # Existing translations are cleaned immediately, even before a future
            # retranslation, so the archive benefits from the new typography/glossary.
            item["title_fa"] = polish_persian(previous.get("title_fa", ""))
            item["summary_fa"] = polish_persian(previous.get("summary_fa", ""))
            item["report_fa"] = polish_persian(previous.get("report_fa", previous.get("summary_fa", "")))
            item["report_coverage"] = previous.get("report_coverage") or coverage_label(source_chars)
            item["translation"] = _meta("translated", (previous.get("translation") or {}).get("engine") or "http-en-fa")
            stats.reused += 1
            continue

        if same_source_text:
            item["title_fa"] = polish_persian(previous.get("title_fa", ""))
            item["summary_fa"] = polish_persian(previous.get("summary_fa", ""))
            item["report_fa"] = polish_persian(previous.get("report_fa", ""))
        else:
            item["title_fa"] = ""
            item["summary_fa"] = ""
            item["report_fa"] = ""
        item["report_coverage"] = coverage_label(source_chars)
        item["translation"] = _meta("queued", "http-en-fa")
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
            item["title_fa"] = polish_persian(title_fa or item.get("title_fa", ""))
            item["summary_fa"] = polish_persian(summary_fa or item.get("summary_fa", ""))
            item["report_fa"] = polish_persian(report_fa or item.get("summary_fa", ""))
            item["report_coverage"] = coverage_label(item.get("source_detail_chars"))
            item["translation"] = _meta("translated", "http-en-fa")
            stats.translated += 1
            consecutive_failures = 0
        except Exception as exc:
            item["translation"] = {
                **_meta("failed", "http-en-fa"),
                "error": str(exc)[:160],
            }
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
