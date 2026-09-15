from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

USER_AGENT = "FoodIndustryIntelligence/1.0 (+https://github.com/nimania/restaurant-intelligence)"
DEFAULT_BODY_LIMIT = 18
MAX_HTML_BYTES = 2_000_000
MAX_ARTICLE_CHARS = 20_000
MAX_REPORT_SOURCE_CHARS = 3_200
MIN_ARTICLE_CHARS = 550
MIN_PARAGRAPHS = 3

BOILERPLATE = (
    "sign up", "subscribe", "newsletter", "cookie", "privacy policy", "terms of use",
    "all rights reserved", "advertisement", "sponsored content", "related articles",
    "recommended for you", "follow us", "share this article", "read more",
)

FACT_TERMS = (
    "said", "says", "announced", "reported", "according", "will", "plans", "expects",
    "launched", "launches", "acquired", "acquisition", "opened", "opening", "closed",
    "increase", "decrease", "grew", "growth", "sales", "revenue", "price", "cost",
    "employees", "stores", "restaurants", "locations", "recall", "outbreak", "FDA",
    "because", "due to", "as a result", "strategy", "investment", "technology",
)


@dataclass
class BodyReaderStats:
    attempted: int = 0
    extracted: int = 0
    blocked: int = 0
    failed: int = 0
    short: int = 0
    reused: int = 0
    queued: int = 0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _body_limit() -> int:
    try:
        return max(0, int(os.getenv("FOOD_INTEL_BODY_READER_LIMIT", DEFAULT_BODY_LIMIT)))
    except (TypeError, ValueError):
        return DEFAULT_BODY_LIMIT


def _clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def _jsonld_article_bodies(soup: BeautifulSoup) -> list[str]:
    found: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            body = node.get("articleBody")
            if isinstance(body, str) and len(_clean(body)) >= MIN_ARTICLE_CHARS:
                found.append(_clean(body))
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for script in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        try:
            walk(json.loads(raw))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    return found


def _usable_paragraph(text: str) -> bool:
    value = _clean(text)
    if len(value) < 45:
        return False
    low = value.lower()
    return not any(term in low for term in BOILERPLATE)


def _paragraphs_from(node) -> list[str]:
    paragraphs: list[str] = []
    seen: set[str] = set()
    for p in node.find_all("p"):
        text = _clean(p.get_text(" ", strip=True))
        key = text.lower()
        if not _usable_paragraph(text) or key in seen:
            continue
        seen.add(key)
        paragraphs.append(text)
    return paragraphs


def extract_article_text(html_text: str) -> tuple[str, str, int]:
    """Extract likely article prose from HTML.

    Returns (text, extractor, paragraph_count). The caller may use the text transiently,
    but it must not be persisted in the public dataset.
    """
    soup = BeautifulSoup(html_text, "html.parser")

    jsonld = _jsonld_article_bodies(soup)
    if jsonld:
        text = max(jsonld, key=len)[:MAX_ARTICLE_CHARS]
        return text, "jsonld.articleBody", max(1, len(re.split(r"\n{2,}", text)))

    for tag in soup(["script", "style", "nav", "footer", "header", "form", "aside", "noscript", "svg"]):
        tag.decompose()

    selectors = [
        "article",
        "main",
        "[itemprop='articleBody']",
        ".article-body", ".article-content", ".entry-content", ".post-content",
        ".story-body", ".story-content", ".content-body", ".article__body",
    ]
    candidates = []
    for selector in selectors:
        for node in soup.select(selector):
            paragraphs = _paragraphs_from(node)
            chars = sum(len(x) for x in paragraphs)
            if chars:
                candidates.append((chars, len(paragraphs), selector, paragraphs))

    if not candidates:
        for node in soup.find_all(["div", "section"], limit=250):
            paragraphs = _paragraphs_from(node)
            chars = sum(len(x) for x in paragraphs)
            if chars >= MIN_ARTICLE_CHARS:
                candidates.append((chars, len(paragraphs), "scored-container", paragraphs))

    if not candidates:
        return "", "none", 0

    chars, count, extractor, paragraphs = max(candidates, key=lambda x: (x[0], x[1]))
    text = "\n\n".join(paragraphs)[:MAX_ARTICLE_CHARS]
    return text, extractor, count


def _sentence_tokens(text: str) -> set[str]:
    return {x for x in re.findall(r"[\w%$€£]+", text.lower(), flags=re.UNICODE) if len(x) > 2}


def _too_similar(text: str, selected: list[str]) -> bool:
    a = _sentence_tokens(text)
    if not a:
        return True
    for other in selected:
        b = _sentence_tokens(other)
        union = len(a | b)
        if union and len(a & b) / union >= 0.72:
            return True
    return False


def select_report_source(article_text: str) -> tuple[str, int]:
    """Choose a fact-dense subset for a comprehensive summary, not a full republication."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", article_text) if _usable_paragraph(p)]
    sentences: list[tuple[int, str, float]] = []
    ordinal = 0
    for p_index, paragraph in enumerate(paragraphs):
        chunks = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“])|(?<=[؟!。])\s+", paragraph)
        for s_index, raw in enumerate(chunks):
            sentence = _clean(raw)
            if len(sentence) < 45:
                continue
            score = 0.0
            if p_index == 0:
                score += 7
            elif p_index == 1:
                score += 4
            if s_index == 0:
                score += 1
            if re.search(r"\d", sentence):
                score += 4
            if re.search(r"[%$€£]|million|billion|percent|درصد|میلیون|میلیارد", sentence, re.I):
                score += 3
            low = sentence.lower()
            score += min(6, sum(1 for term in FACT_TERMS if term.lower() in low) * 1.5)
            if 65 <= len(sentence) <= 330:
                score += 1
            sentences.append((ordinal, sentence, score))
            ordinal += 1

    if not sentences:
        return _clean(article_text)[:MAX_REPORT_SOURCE_CHARS], 0

    # Preserve the lead, then fill with the most fact-dense non-duplicate sentences.
    ranked = sorted(sentences, key=lambda x: (-x[2], x[0]))
    chosen: list[tuple[int, str, float]] = []
    chosen_texts: list[str] = []
    total = 0
    for row in ranked:
        _, sentence, _ = row
        if _too_similar(sentence, chosen_texts):
            continue
        if total + len(sentence) > MAX_REPORT_SOURCE_CHARS:
            continue
        chosen.append(row)
        chosen_texts.append(sentence)
        total += len(sentence) + 1
        if len(chosen) >= 12:
            break

    chosen.sort(key=lambda x: x[0])
    return " ".join(x[1] for x in chosen), len(chosen)


class ArticleBodyReader:
    def __init__(self, timeout: int = 7) -> None:
        self.timeout = timeout
        self._robots: dict[str, RobotFileParser | bool] = {}

    def _robots_parser(self, url: str) -> RobotFileParser | bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin in self._robots:
            return self._robots[origin]
        robots_url = urljoin(origin + "/", "robots.txt")
        request = Request(robots_url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*"})
        try:
            with urlopen(request, timeout=min(self.timeout, 5)) as response:
                raw = response.read(250_000).decode("utf-8", errors="replace")
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(raw.splitlines())
            self._robots[origin] = parser
            return parser
        except HTTPError as exc:
            # Missing robots.txt means no published crawl restriction. Explicit access
            # denials are treated conservatively as blocked.
            allowed = exc.code in (404, 410)
            self._robots[origin] = allowed
            return allowed
        except (URLError, TimeoutError, OSError):
            self._robots[origin] = False
            return False

    def allowed(self, url: str) -> bool:
        parser = self._robots_parser(url)
        if isinstance(parser, bool):
            return parser
        return parser.can_fetch(USER_AGENT, url)

    def fetch(self, url: str) -> tuple[str, dict]:
        if not self.allowed(url):
            return "", {"status": "blocked", "fetched_at": utc_now()}

        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
                "Accept-Language": "en,fa;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content_type = (response.headers.get("Content-Type") or "").lower()
                if "html" not in content_type:
                    return "", {"status": "non-html", "fetched_at": utc_now()}
                raw = response.read(MAX_HTML_BYTES + 1)
                if len(raw) > MAX_HTML_BYTES:
                    return "", {"status": "too-large", "fetched_at": utc_now()}
                charset = response.headers.get_content_charset() or "utf-8"
                html_text = raw.decode(charset, errors="replace")
        except HTTPError as exc:
            return "", {"status": "http-error", "http_status": exc.code, "fetched_at": utc_now()}
        except (URLError, TimeoutError, OSError) as exc:
            return "", {"status": "network-error", "error": str(exc)[:120], "fetched_at": utc_now()}

        article_text, extractor, paragraphs = extract_article_text(html_text)
        if len(article_text) < MIN_ARTICLE_CHARS or paragraphs < MIN_PARAGRAPHS:
            return "", {
                "status": "short",
                "chars": len(article_text),
                "paragraphs": paragraphs,
                "extractor": extractor,
                "fetched_at": utc_now(),
            }

        report_source, selected_sentences = select_report_source(article_text)
        if len(report_source) < 300:
            return "", {
                "status": "short",
                "chars": len(article_text),
                "paragraphs": paragraphs,
                "extractor": extractor,
                "fetched_at": utc_now(),
            }

        meta = {
            "status": "extracted",
            "chars": len(article_text),
            "paragraphs": paragraphs,
            "selected_sentences": selected_sentences,
            "selected_chars": len(report_source),
            "extractor": extractor,
            "content_hash": _content_hash(article_text),
            "fetched_at": utc_now(),
        }
        return report_source, meta


def enrich_article_bodies(items: list[dict], previous_by_id: dict[str, dict] | None = None) -> BodyReaderStats:
    previous_by_id = previous_by_id or {}
    stats = BodyReaderStats()
    reader = ArticleBodyReader()

    candidates: list[dict] = []
    for item in items:
        previous = previous_by_id.get(item.get("id", ""), {})
        previous_meta = previous.get("article_body") or {}
        if (
            previous_meta.get("status") == "extracted"
            and previous.get("report_fa")
            and previous.get("report_source_kind") == "article_body"
        ):
            for field in ("article_body", "report_source_kind", "report_source_chars", "report_selected_chars"):
                if previous.get(field) is not None:
                    item[field] = previous.get(field)
            stats.reused += 1
            continue

        url = item.get("url") or ""
        if not url.startswith(("http://", "https://")) or item.get("source", {}).get("aggregator"):
            continue
        candidates.append(item)

    candidates.sort(
        key=lambda x: (
            x.get("relevance_score") or 0,
            x.get("iran_relevance_score") or 0,
            x.get("published_at") or "",
        ),
        reverse=True,
    )

    limit = _body_limit()
    for index, item in enumerate(candidates):
        if index >= limit:
            stats.queued += 1
            continue
        stats.attempted += 1
        report_source, meta = reader.fetch(item["url"])
        item["article_body"] = meta
        status = meta.get("status")
        if status == "extracted":
            item["_report_source"] = report_source
            item["report_source_kind"] = "article_body"
            item["report_source_chars"] = meta.get("chars", 0)
            item["report_selected_chars"] = meta.get("selected_chars", 0)
            stats.extracted += 1
        elif status == "blocked":
            stats.blocked += 1
        elif status == "short":
            stats.short += 1
        else:
            stats.failed += 1

    return stats
