from __future__ import annotations

import re
from dataclasses import dataclass

PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")


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


class PersianTranslator:
    """Offline English→Persian translator backed by Argos Translate."""

    def __init__(self) -> None:
        self._translation = None

    def _ensure_translation(self):
        if self._translation is not None:
            return self._translation

        import argostranslate.package
        import argostranslate.translate

        translation = argostranslate.translate.get_translation_from_codes("en", "fa")
        if translation is None:
            argostranslate.package.update_package_index()
            packages = argostranslate.package.get_available_packages()
            package = next(
                p for p in packages
                if p.from_code == "en" and p.to_code == "fa"
            )
            argostranslate.package.install_from_path(package.download())
            translation = argostranslate.translate.get_translation_from_codes("en", "fa")

        if translation is None:
            raise RuntimeError("Argos English→Persian translation package is unavailable")

        self._translation = translation
        return translation

    def translate(self, text: str, limit: int) -> str:
        text = compact(text, limit)
        if not text:
            return ""
        if looks_persian(text):
            return text
        translation = self._ensure_translation()
        return compact(translation.translate(text), limit + 180)


def apply_persian_translation(items: list[dict], previous_by_id: dict[str, dict] | None = None) -> TranslationStats:
    previous_by_id = previous_by_id or {}
    stats = TranslationStats()
    translator = PersianTranslator()

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
                "engine": "argos-en-fa",
            }
            stats.reused += 1
            continue

        try:
            item["title_fa"] = translator.translate(title, 240)
            item["summary_fa"] = translator.translate(summary, 520) if summary else ""
            item["translation"] = {"status": "translated", "engine": "argos-en-fa"}
            stats.translated += 1
        except Exception as exc:
            item["title_fa"] = ""
            item["summary_fa"] = ""
            item["translation"] = {
                "status": "failed",
                "engine": "argos-en-fa",
                "error": str(exc)[:160],
            }
            stats.failed += 1

    return stats
