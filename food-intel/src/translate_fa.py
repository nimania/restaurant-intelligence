from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")
DEFAULT_TRANSLATION_LIMIT = 180
MAX_CONSECUTIVE_FAILURES = 4
GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
MYMEMORY_ENDPOINT = "https://api.mymemory.translated.net/get"
SPLIT_MARKER = "[[[NIMA_SPLIT_9F7C]]]"


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


@dataclass
class TranslationStats:
    translated: int = 0
    reused: int = 0
    persian_original: int = 0
    failed: int = 0
    queued: int = 0


class PersianTranslator:
    """Lightweight HTTP English→Persian translator with a no-key fallback.

    Successful translations are persisted in news.json and reused. Translation is a
    best-effort enrichment: network/rate-limit problems never block news collection.
    """

    def __init__(self, timeout: int = 4, pause: float = 0.08) -> None:
        self.timeout = timeout
        self.pause = pause

    def _read_json(self, url: str) -> object:
        request = Request(
            url,
            headers={
                "User-Agent": "FoodIndustryIntelligence/0.6 (+https://github.com/nimania/restaurant-intelligence)",
                "Accept": "application/json,text/plain,*/*",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _google(self, text: str) -> str:
        query = urlencode({
            "client": "gtx",
            "sl": "en",
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
        # MyMemory limits a single q parameter to roughly 500 bytes.
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
        text = compact(text, limit)
        if not text:
            return ""
        if looks_persian(text):
            return text

        last_error: Exception | None = None
        for engine in (self._google, self._mymemory):
            try:
                translated = engine(text)
                if translated and looks_persian(translated):
                    time.sleep(self.pause)
                    return compact(translated, limit + 180)
                last_error = RuntimeError("translation result is not Persian")
            except Exception as exc:
                last_error = exc
        raise RuntimeError(str(last_error or "translation failed"))

    def translate_article(self, title: str, summary: str) -> tuple[str, str]:
        title = compact(title, 240)
        summary = compact(summary, 520)
        if not summary:
            return self.translate(title, 240), ""

        combined = f"{title}\n\n{SPLIT_MARKER}\n\n{summary}"
        try:
            translated = self.translate(combined, 820)
            if SPLIT_MARKER in translated:
                title_fa, summary_fa = translated.split(SPLIT_MARKER, 1)
                title_fa = compact(title_fa, 420).strip()
                summary_fa = compact(summary_fa, 700).strip()
                if title_fa and looks_persian(title_fa):
                    return title_fa, summary_fa
        except Exception:
            pass

        return self.translate(title, 240), self.translate(summary, 520)


def _translation_limit() -> int:
    try:
        return max(0, int(os.getenv("FOOD_INTEL_TRANSLATION_LIMIT", DEFAULT_TRANSLATION_LIMIT)))
    except (TypeError, ValueError):
        return DEFAULT_TRANSLATION_LIMIT


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

        if item.get("language") == "fa" or looks_persian(title):
            item["title_fa"] = title
            item["summary_fa"] = compact(summary, 520)
            item["translation"] = {"status": "original-fa", "engine": None}
            stats.persian_original += 1
            continue

        same_source_text = (
            previous.get("title") == title
            and previous.get("summary") == summary
            and previous.get("title_fa")
        )
        if same_source_text:
            item["title_fa"] = previous.get("title_fa")
            item["summary_fa"] = previous.get("summary_fa", "")
            item["translation"] = previous.get("translation") or {
                "status": "translated",
                "engine": "http-en-fa",
            }
            stats.reused += 1
            continue

        item["title_fa"] = ""
        item["summary_fa"] = ""
        item["translation"] = {"status": "queued", "engine": "http-en-fa"}
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
            title_fa, summary_fa = translator.translate_article(
                item.get("title", ""), item.get("summary", "")
            )
            item["title_fa"] = title_fa
            item["summary_fa"] = summary_fa
            item["translation"] = {"status": "translated", "engine": "http-en-fa"}
            stats.translated += 1
            consecutive_failures = 0
        except Exception as exc:
            item["translation"] = {
                "status": "failed",
                "engine": "http-en-fa",
                "error": str(exc)[:160],
            }
            stats.failed += 1
            consecutive_failures += 1

            # If the external service is unavailable, fail fast. All untouched items
            # remain queued and will be retried automatically next run.
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                remaining = min(limit, len(pending)) - index - 1
                if remaining > 0:
                    stats.queued += remaining
                if len(pending) > limit:
                    stats.queued += len(pending) - limit
                break

    return stats
