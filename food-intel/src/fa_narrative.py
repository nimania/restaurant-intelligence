from __future__ import annotations

import re

from fa_editor import editorialize_report, editorialize_summary
from fa_polish import polish_persian

MAX_NARRATIVE_WORDS = 230
SOURCE_CHUNK_CHARS = 380
MAX_SOURCE_CHUNKS = 8
SENTENCE_RE = re.compile(r"(?<=[.!؟!])\s+")


def _tokens(text: str) -> set[str]:
    value = re.sub(r"[^\w\u0600-\u06FF]+", " ", polish_persian(text).lower())
    return {x for x in value.split() if len(x) > 1}


def _similar(a: str, b: str) -> float:
    aa, bb = _tokens(a), _tokens(b)
    if not aa or not bb:
        return 0.0
    return (2 * len(aa & bb)) / (len(aa) + len(bb))


def source_chunks(text: str) -> list[str]:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return []
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", value) if x.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= SOURCE_CHUNK_CHARS:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = sentence
        if len(chunks) >= MAX_SOURCE_CHUNKS:
            break
    if current and len(chunks) < MAX_SOURCE_CHUNKS:
        chunks.append(current)
    return chunks[:MAX_SOURCE_CHUNKS]


def _distinct_sentences(text: str, title_fa: str = "") -> list[str]:
    value = editorialize_report(polish_persian(text), sentences_per_paragraph=1)
    raw = [x.strip() for x in re.split(r"\n+|(?<=[.!؟!])\s+", value) if x.strip()]
    out: list[str] = []
    for sentence in raw:
        if len(sentence) < 18:
            continue
        if title_fa and _similar(sentence, title_fa) >= 0.88:
            continue
        if any(_similar(sentence, old) >= 0.82 for old in out):
            continue
        out.append(sentence)
    return out


def _trim_sentences(sentences: list[str], max_words: int = MAX_NARRATIVE_WORDS) -> list[str]:
    out: list[str] = []
    used = 0
    for sentence in sentences:
        words = sentence.split()
        if out and used + len(words) > max_words:
            break
        if not out and len(words) > max_words:
            out.append(" ".join(words[:max_words]).rstrip("،؛,:-. ") + "…")
            break
        out.append(sentence)
        used += len(words)
    return out


def build_narrative(translated_parts: list[str], title_fa: str = "") -> tuple[str, str]:
    """Build a readable Persian news narrative from separately translated source chunks.

    The function does not invent transitions or analysis. It keeps source order,
    removes near-duplicates, preserves factual sentences, and formats them as short
    newsroom paragraphs. Returns (narrative, short_summary).
    """
    merged = " ".join(polish_persian(x) for x in translated_parts if x).strip()
    if not merged:
        return "", ""

    sentences = _trim_sentences(_distinct_sentences(merged, title_fa))
    if not sentences:
        return "", ""

    paragraphs: list[str] = []
    for i in range(0, len(sentences), 2):
        paragraphs.append(" ".join(sentences[i : i + 2]).strip())
    narrative = "\n\n".join(paragraphs)
    narrative = editorialize_report(narrative, sentences_per_paragraph=2)
    summary = editorialize_summary(" ".join(sentences[:3]), max_sentences=3)
    return narrative.strip(), summary.strip()
