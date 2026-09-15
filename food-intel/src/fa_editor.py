from __future__ import annotations

import re

from fa_polish import polish_persian

EDITORIAL_VERSION = 1

# Conservative newsroom-style replacements. These improve machine-translation prose
# without changing numbers, proper nouns, uncertainty, or factual relationships.
PHRASE_RULES: list[tuple[str, str]] = [
    (r"\bدر حال حاضر\b", "اکنون"),
    (r"\bبه منظور\b", "برای"),
    (r"\bبه دنبال این است که\b", "می‌خواهد"),
    (r"\bدر تلاش است تا\b", "می‌کوشد"),
    (r"\bقرار است تا\b", "قرار است"),
    (r"\bبا توجه به این واقعیت که\b", "با توجه به اینکه"),
    (r"\bبا وجود این واقعیت که\b", "با وجود اینکه"),
    (r"\bدر نتیجه این امر\b", "در نتیجه"),
    (r"\bاین شرکت گفت که\b", "این شرکت اعلام کرد"),
    (r"\bاین شرکت گفته است که\b", "این شرکت اعلام کرده است"),
    (r"\bاین شرکت می‌گوید که\b", "این شرکت می‌گوید"),
    (r"\bاعلام کرد که قصد دارد\b", "اعلام کرد قصد دارد"),
    (r"\bاعلام کرده است که قصد دارد\b", "اعلام کرده است قصد دارد"),
    (r"\bگفت که قصد دارد\b", "گفت قصد دارد"),
    (r"\bبه عنوان بخشی از\b", "در چارچوب"),
    (r"\bدر رابطه با\b", "درباره"),
    (r"\bدر زمینهٔ\b", "در حوزهٔ"),
    (r"\bدر زمینه\b", "در حوزه"),
    (r"\bمورد استفاده قرار می‌دهد\b", "استفاده می‌کند"),
    (r"\bمورد استفاده قرار خواهد داد\b", "استفاده خواهد کرد"),
    (r"\bارائه خواهد نمود\b", "ارائه خواهد کرد"),
    (r"\bاعلام نمود\b", "اعلام کرد"),
    (r"\bمی‌باشد\b", "است"),
    (r"\bمی باشد\b", "است"),
]

CONNECTOR_SPLITS: list[tuple[str, str]] = [
    ("؛ ", ""),
    ("، اما ", "اما "),
    ("، با این حال ", "با این حال، "),
    ("، همچنین ", "همچنین، "),
    ("، در همین حال ", "در همین حال، "),
    ("، از سوی دیگر ", "از سوی دیگر، "),
]

SENTENCE_RE = re.compile(r"(?<=[.!؟!])\s+")


def _apply_phrase_rules(text: str) -> str:
    value = text
    for pattern, replacement in PHRASE_RULES:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    return value


def _sentence_case_cleanup(sentence: str) -> str:
    value = sentence.strip()
    value = re.sub(r"^(?:و|همچنین)\s+همچنین\s+", "همچنین ", value)
    value = re.sub(r"^(?:اما|ولی)\s+(?:اما|ولی)\s+", "اما ", value)
    value = re.sub(r"\s+([،؛؟!,.])", r"\1", value)
    value = re.sub(r"([،؛؟!,.]){2,}", r"\1", value)
    return value.strip()


def _split_long_sentence(sentence: str, max_chars: int = 210) -> list[str]:
    sentence = sentence.strip()
    if len(sentence) <= max_chars:
        return [sentence]

    candidates: list[tuple[int, str, str]] = []
    for marker, lead in CONNECTOR_SPLITS:
        start = 70
        while True:
            pos = sentence.find(marker, start)
            if pos < 0:
                break
            right_start = pos + len(marker)
            left_len = pos
            right_len = len(sentence) - right_start
            if left_len >= 65 and right_len >= 45:
                score = abs(pos - len(sentence) // 2)
                candidates.append((score, marker, lead))
            start = pos + len(marker)

    if not candidates:
        return [sentence]

    _, marker, lead = min(candidates, key=lambda x: x[0])
    pos = sentence.find(marker, 65)
    left = sentence[:pos].rstrip(" ،؛")
    right = sentence[pos + len(marker):].strip()
    if not left or not right:
        return [sentence]
    left = left.rstrip(".!؟!") + "."
    right = (lead + right).strip()
    return [_sentence_case_cleanup(left), _sentence_case_cleanup(right)]


def _sentences(text: str) -> list[str]:
    value = polish_persian(text)
    if not value:
        return []
    raw = [x.strip() for x in SENTENCE_RE.split(value) if x.strip()]
    result: list[str] = []
    for sentence in raw:
        result.extend(_split_long_sentence(_sentence_case_cleanup(sentence)))
    return [x for x in result if x]


def editorialize_title(text: str) -> str:
    value = _apply_phrase_rules(polish_persian(text))
    value = re.sub(r"^این شرکت\s+", "", value)
    value = re.sub(r"\s+است:\s*", ": ", value)
    value = re.sub(r"\s{2,}", " ", value)
    return value.strip()


def editorialize_summary(text: str, max_sentences: int = 3) -> str:
    value = _apply_phrase_rules(polish_persian(text))
    sentences = _sentences(value)
    return " ".join(sentences[:max_sentences]).strip()


def editorialize_report(text: str, sentences_per_paragraph: int = 2) -> str:
    value = _apply_phrase_rules(polish_persian(text))
    sentences = _sentences(value)
    if not sentences:
        return ""
    paragraphs: list[str] = []
    for i in range(0, len(sentences), max(1, sentences_per_paragraph)):
        paragraphs.append(" ".join(sentences[i : i + sentences_per_paragraph]).strip())
    return "\n\n".join(x for x in paragraphs if x)


def editorial_meta(status: str = "edited") -> dict:
    return {
        "status": status,
        "version": EDITORIAL_VERSION,
        "mode": "conservative-fa-newsroom",
    }
