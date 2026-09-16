from __future__ import annotations

import re

from fa_editor import editorialize_report, editorialize_summary
from fa_polish import polish_persian

MAX_NARRATIVE_WORDS = 320
MAX_SOURCE_UNITS = 10
MAX_UNIT_CHARS = 300


def _tokens(text: str) -> set[str]:
    value = re.sub(r"[^\w\u0600-\u06FF]+", " ", polish_persian(text).lower())
    return {x for x in value.split() if len(x) > 1}


def _similar(a: str, b: str) -> float:
    aa, bb = _tokens(a), _tokens(b)
    if not aa or not bb:
        return 0.0
    return (2 * len(aa & bb)) / (len(aa) + len(bb))


def source_chunks(text: str) -> list[str]:
    """Return short source units for faithful sentence-level translation.

    Units stay in source order. Long source sentences are clipped at a clause boundary
    rather than merged into a large paragraph. This reduces the syntax drift seen when
    generic MT receives long newsroom paragraphs.
    """
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return []
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", value) if x.strip()]
    units: list[str] = []
    for sentence in sentences:
        if len(units) >= MAX_SOURCE_UNITS:
            break
        if len(sentence) <= MAX_UNIT_CHARS:
            units.append(sentence)
            continue
        clauses = [x.strip() for x in re.split(r"(?<=[,;:])\s+", sentence) if x.strip()]
        current = ""
        for clause in clauses:
            candidate = f"{current} {clause}".strip()
            if len(candidate) <= MAX_UNIT_CHARS:
                current = candidate
            else:
                if current:
                    units.append(current)
                current = clause[:MAX_UNIT_CHARS]
                if len(units) >= MAX_SOURCE_UNITS:
                    break
        if current and len(units) < MAX_SOURCE_UNITS:
            units.append(current)
    return units[:MAX_SOURCE_UNITS]


def _distinct_sentences(parts: list[str], title_fa: str = "") -> list[str]:
    out: list[str] = []
    for part in parts:
        value = editorialize_report(polish_persian(part), sentences_per_paragraph=1)
        raw = [x.strip() for x in re.split(r"\n+|(?<=[.!؟!])\s+", value) if x.strip()]
        for sentence in raw:
            if len(sentence) < 18:
                continue
            if title_fa and _similar(sentence, title_fa) >= 0.90:
                continue
            if any(_similar(sentence, old) >= 0.84 for old in out):
                continue
            out.append(sentence)
    return out


def _trim(sentences: list[str], max_words: int = MAX_NARRATIVE_WORDS) -> list[str]:
    out, used = [], 0
    for sentence in sentences:
        words = sentence.split()
        if out and used + len(words) > max_words:
            break
        out.append(sentence if len(words) <= max_words else " ".join(words[:max_words]).rstrip("،؛,:-. ") + "…")
        used += min(len(words), max_words)
    return out


def build_narrative(translated_parts: list[str], title_fa: str = "") -> tuple[str, str]:
    """Build a source-faithful Persian report plus a 30-second recap.

    No analysis or invented transitions are added. The report is a reordered-by-source
    reconstruction of translated factual units; the recap is a compact selection from
    the first distinct facts. Returns (report_fa, recap_fa).
    """
    sentences = _trim(_distinct_sentences([x for x in translated_parts if x], title_fa))
    if not sentences:
        return "", ""
    paragraphs = [" ".join(sentences[i:i + 2]).strip() for i in range(0, len(sentences), 2)]
    report = editorialize_report("\n\n".join(paragraphs), sentences_per_paragraph=2).strip()
    recap = editorialize_summary(" ".join(sentences[:4]), max_sentences=4).strip()
    recap_words = recap.split()
    if len(recap_words) > 105:
        recap = " ".join(recap_words[:105]).rstrip("،؛,:-. ") + "…"
    return report, recap
