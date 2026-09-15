from __future__ import annotations

import re
from dataclasses import dataclass, asdict

QUALITY_VERSION = 1
PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
WORD_RE = re.compile(r"[\u0600-\u06FFA-Za-z0-9٪%$€£¥]+")
SENTENCE_RE = re.compile(r"(?<=[.!؟!])\s+")
HTML_RE = re.compile(r"<[^>]+>")
PLACEHOLDER_RE = re.compile(r"\[\[\[|NIMA_SPLIT|undefined|null|translation failed|unexpected primary", re.I)


@dataclass
class TextQuality:
    score: int
    status: str
    issues: list[str]
    persian_ratio: float
    latin_ratio: float
    max_sentence_chars: int
    word_count: int


def _letter_ratios(text: str) -> tuple[float, float]:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0, 0.0
    fa = len(PERSIAN_RE.findall(text))
    latin = len(LATIN_RE.findall(text))
    total = max(len(letters), 1)
    return fa / total, latin / total


def _repetition_penalty(words: list[str]) -> tuple[int, bool]:
    if len(words) < 10:
        return 0, False
    lowered = [w.lower() for w in words]
    repeated = 0
    for size in (2, 3, 4):
        seen: dict[tuple[str, ...], int] = {}
        for i in range(len(lowered) - size + 1):
            chunk = tuple(lowered[i : i + size])
            seen[chunk] = seen.get(chunk, 0) + 1
        repeated += sum(v - 1 for v in seen.values() if v >= 3)
    if repeated >= 5:
        return 18, True
    if repeated >= 2:
        return 9, True
    return 0, False


def assess_text(text: str, *, kind: str = "summary") -> TextQuality:
    value = str(text or "").strip()
    issues: list[str] = []
    if not value:
        return TextQuality(0, "block", ["empty"], 0.0, 0.0, 0, 0)

    score = 100
    fa_ratio, latin_ratio = _letter_ratios(value)
    words = WORD_RE.findall(value)
    sentences = [x.strip() for x in SENTENCE_RE.split(value) if x.strip()]
    max_sentence = max((len(x) for x in sentences), default=len(value))

    if HTML_RE.search(value):
        score -= 24
        issues.append("html")
    if PLACEHOLDER_RE.search(value):
        score -= 45
        issues.append("placeholder")
    if "�" in value:
        score -= 35
        issues.append("broken-character")

    if kind != "title" and len(words) < 7:
        score -= 18
        issues.append("too-short")
    if kind == "title" and len(words) < 2:
        score -= 25
        issues.append("title-too-short")

    # Persian editorial output may legitimately retain short model/product names in
    # Latin script, but a high Latin share usually signals an untranslated fragment.
    latin_limit = 0.28 if kind == "title" else 0.20
    if latin_ratio > 0.45:
        score -= 42
        issues.append("mostly-latin")
    elif latin_ratio > latin_limit:
        score -= 20
        issues.append("too-much-latin")

    if fa_ratio < 0.42:
        score -= 32
        issues.append("low-persian-ratio")
    elif fa_ratio < 0.62:
        score -= 12
        issues.append("mixed-script")

    sentence_limit = 175 if kind == "summary" else 225
    if kind == "title":
        sentence_limit = 155
    if max_sentence > sentence_limit * 1.7:
        score -= 24
        issues.append("very-long-sentence")
    elif max_sentence > sentence_limit:
        score -= 11
        issues.append("long-sentence")

    rep_penalty, repeated = _repetition_penalty(words)
    score -= rep_penalty
    if repeated:
        issues.append("repetition")

    if re.search(r"([،؛,.!?؟])\1{1,}", value):
        score -= 9
        issues.append("duplicate-punctuation")
    if re.search(r"\b(و|که|از|به|در)\s+\1\b", value):
        score -= 9
        issues.append("duplicate-word")

    score = max(0, min(100, score))
    if score < 45:
        status = "block"
    elif score < 68:
        status = "retry"
    elif score < 82:
        status = "warn"
    else:
        status = "pass"
    return TextQuality(score, status, issues, round(fa_ratio, 3), round(latin_ratio, 3), max_sentence, len(words))


def assess_item(item: dict) -> dict:
    if item.get("language") == "fa" or (item.get("translation") or {}).get("status") == "original-fa":
        return {
            "version": QUALITY_VERSION,
            "status": "pass",
            "score": 100,
            "publishable": True,
            "issues": [],
            "parts": {},
            "source_original_fa": True,
        }

    title = assess_text(item.get("title_fa", ""), kind="title")
    summary = assess_text(item.get("summary_fa", ""), kind="summary")
    report_text = item.get("report_fa") or item.get("summary_fa") or ""
    report = assess_text(report_text, kind="report")

    # Title failure is critical. Otherwise weight title and summary slightly more than
    # the deep report because they determine feed readability.
    weighted = round(title.score * 0.36 + summary.score * 0.34 + report.score * 0.30)
    issues = sorted(set(title.issues + summary.issues + report.issues))
    if title.status == "block" or weighted < 45:
        status = "block"
    elif title.status == "retry" or summary.status in {"block", "retry"} or weighted < 68:
        status = "retry"
    elif weighted < 82 or "warn" in {title.status, summary.status, report.status}:
        status = "warn"
    else:
        status = "pass"

    return {
        "version": QUALITY_VERSION,
        "status": status,
        "score": weighted,
        "publishable": status in {"pass", "warn"},
        "issues": issues,
        "parts": {
            "title": asdict(title),
            "summary": asdict(summary),
            "report": asdict(report),
        },
        "source_original_fa": False,
    }


def quality_stats(items: list[dict]) -> dict:
    counts = {"pass": 0, "warn": 0, "retry": 0, "block": 0}
    for item in items:
        quality = item.get("translation_quality") or assess_item(item)
        status = quality.get("status", "block")
        counts[status] = counts.get(status, 0) + 1
    counts["publishable"] = counts.get("pass", 0) + counts.get("warn", 0)
    counts["total"] = len(items)
    return counts
