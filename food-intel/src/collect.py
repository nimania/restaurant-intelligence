from __future__ import annotations

import calendar
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import yaml
from dateutil import parser as date_parser

from classify import classify
from classify_fa import classify_fa
from entities import detect_brands, load_brands
from score import relevance_score
from signals import build_signals

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = [
    ROOT / "config" / "sources.yml",
    ROOT / "config" / "sources_iran.yml",
    ROOT / "config" / "sources_iran_discovery.yml",
]
DATA_PATH = ROOT / "data" / "news.json"
SIGNALS_PATH = ROOT / "data" / "signals.json"
MAX_ITEMS = 5000
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "gclid", "fbclid", "mc_cid", "mc_eid",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def search_normalize(value: str | None) -> str:
    return re.sub(
        r"\s+",
        " ",
        (value or "")
        .lower()
        .replace("\u200c", " ")
        .replace("ي", "ی")
        .replace("ك", "ک"),
    ).strip()


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def article_id(url: str, title: str, source_id: str) -> str:
    seed = url or f"{source_id}|{title.strip().lower()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]


def entry_datetime(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        value = getattr(entry, attr, None)
        if value:
            dt = datetime.fromtimestamp(calendar.timegm(value), tz=timezone.utc)
            return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for attr in ("published", "updated"):
        value = getattr(entry, attr, None)
        if value:
            try:
                dt = date_parser.parse(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            except (ValueError, TypeError, OverflowError):
                pass
    return utc_now()


def merge_unique(*groups: list[str]) -> list[str]:
    result = []
    for group in groups:
        for value in group:
            if value not in result:
                result.append(value)
    return result


def load_sources() -> list[dict]:
    sources = []
    seen = set()
    for path in SOURCE_PATHS:
        if not path.exists():
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for source in payload.get("sources", []):
            if source.get("id") in seen:
                continue
            seen.add(source.get("id"))
            if source.get("enabled") and source.get("type") == "rss" and source.get("feed_url"):
                sources.append(source)
    return sources


def load_existing() -> dict:
    if not DATA_PATH.exists():
        return {"items": []}
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"items": []}


def source_accepts_entry(entry, source: dict) -> bool:
    include = source.get("include_keywords", []) or []
    exclude = source.get("exclude_keywords", []) or []
    if not include and not exclude:
        return True

    title = clean_text(getattr(entry, "title", ""))
    summary = clean_text(getattr(entry, "summary", "") or getattr(entry, "description", ""))
    text = search_normalize(f"{title} {summary}")

    if include and not any(search_normalize(keyword) in text for keyword in include):
        return False
    if exclude and any(search_normalize(keyword) in text for keyword in exclude):
        return False
    return True


def iran_relevance_score(title: str, summary: str, source: dict, brands: list[dict]) -> int:
    score = 0
    market = (source.get("market") or "").lower()
    country = (source.get("country") or source.get("region") or "").upper()
    language = (source.get("language") or "").lower()
    text = search_normalize(f"{title} {summary}")

    if market == "iran" or country == "IR":
        score = 85
    elif language == "fa":
        score = 60

    if "ایران" in text or "ایرانی" in text or "بازار ایران" in text:
        score = max(score, 70)
        score += 5

    if any((brand.get("market") or "").lower() == "iran" for brand in brands):
        score = max(score, 92)

    high_signal = ["صنایع غذایی", "رستوران", "بسته بندی", "بسته‌بندی", "آشپزخانه صنعتی", "برند غذایی"]
    if score and any(search_normalize(term) in text for term in high_signal):
        score += 5

    return min(score, 100)


def entry_publisher(entry) -> str | None:
    source = getattr(entry, "source", None)
    if hasattr(source, "get"):
        return clean_text(source.get("title") or "") or None
    return None


def normalize_entry(entry, source: dict, brand_catalog: list[dict]) -> dict | None:
    title = clean_text(getattr(entry, "title", ""))
    url = canonicalize_url(getattr(entry, "link", "") or "")
    if not title or not url:
        return None

    summary = clean_text(getattr(entry, "summary", "") or getattr(entry, "description", ""))[:1200]
    categories, topics = classify(title, summary, defaults=source.get("default_categories", []))
    if source.get("language") == "fa":
        fa_categories, fa_topics = classify_fa(title, summary)
        categories = merge_unique(categories, fa_categories)[:10]
        topics = merge_unique(topics, fa_topics)[:14]

    brands = detect_brands(title, summary, brand_catalog)
    iran_score = iran_relevance_score(title, summary, source, brands)
    published_at = entry_datetime(entry)
    source_market = source.get("market") or ("iran" if iran_score >= 70 else None)
    publisher = entry_publisher(entry) if source.get("aggregator") else None

    item = {
        "id": article_id(url, title, source["id"]),
        "title": title,
        "url": url,
        "source": {
            "id": source["id"],
            "name": source["name"],
            "homepage": source.get("homepage"),
            "class": source.get("source_class"),
            "priority": source.get("priority", 3),
            "market": source_market,
            "country": source.get("country"),
            "aggregator": source.get("aggregator"),
        },
        "discovered_publisher": publisher,
        "author": clean_text(getattr(entry, "author", "")) or None,
        "published_at": published_at,
        "collected_at": utc_now(),
        "language": source.get("language", "en"),
        "region": source.get("region"),
        "country": source.get("country"),
        "market": source_market,
        "summary": summary,
        "categories": categories,
        "topics": topics,
        "brands": brands,
        "iran_relevance_score": iran_score,
        "relevance_score": None,
    }
    item["relevance_score"] = relevance_score(item, source)
    return item


def collect_source(source: dict, brand_catalog: list[dict]) -> tuple[list[dict], dict]:
    feed = feedparser.parse(source["feed_url"], agent="FoodIndustryIntelligence/0.5.1 (+GitHub)")
    matched = 0
    status = {
        "source_id": source["id"],
        "name": source["name"],
        "feed_url": source["feed_url"],
        "market": source.get("market"),
        "aggregator": source.get("aggregator"),
        "entries_seen": len(feed.entries),
        "entries_matched": 0,
        "bozo": bool(getattr(feed, "bozo", False)),
    }
    if getattr(feed, "bozo_exception", None):
        status["warning"] = str(feed.bozo_exception)[:300]

    items = []
    for entry in feed.entries:
        if not source_accepts_entry(entry, source):
            continue
        matched += 1
        item = normalize_entry(entry, source, brand_catalog)
        if item:
            items.append(item)
    status["entries_matched"] = matched
    return items, status


def main() -> None:
    sources = load_sources()
    source_by_id = {s["id"]: s for s in sources}
    brand_catalog = load_brands()
    existing = load_existing()
    by_id = {item["id"]: item for item in existing.get("items", []) if item.get("id")}
    source_status = []
    processed = 0

    for source in sources:
        items, status = collect_source(source, brand_catalog)
        source_status.append(status)
        for item in items:
            previous = by_id.get(item["id"])
            if previous:
                item["collected_at"] = previous.get("collected_at", item["collected_at"])
            by_id[item["id"]] = item
            processed += 1

    # Re-enrich the retained dataset so new entity and Iran rules apply immediately.
    for item in by_id.values():
        source = source_by_id.get(item.get("source", {}).get("id"), item.get("source", {}))
        item.pop("summary_fa", None)
        item["brands"] = detect_brands(item.get("title", ""), item.get("summary", ""), brand_catalog)
        item["iran_relevance_score"] = iran_relevance_score(
            item.get("title", ""), item.get("summary", ""), source, item["brands"]
        )
        if source.get("market"):
            item["market"] = source.get("market")
        elif item["iran_relevance_score"] >= 70:
            item["market"] = "iran"
        item["relevance_score"] = relevance_score(item, source)

    items = sorted(
        by_id.values(),
        key=lambda x: (x.get("published_at") or "", x.get("relevance_score") or 0),
        reverse=True,
    )[:MAX_ITEMS]

    generated_at = utc_now()
    iran_items = [item for item in items if item.get("market") == "iran" or (item.get("iran_relevance_score") or 0) >= 70]
    payload = {
        "schema_version": "0.5.1",
        "generated_at": generated_at,
        "count": len(items),
        "iran_count": len(iran_items),
        "active_sources": len(sources),
        "active_iran_sources": sum(1 for s in sources if s.get("market") == "iran"),
        "entries_processed_this_run": processed,
        "source_status": source_status,
        "items": items,
    }
    signals = build_signals(items, generated_at)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SIGNALS_PATH.write_text(json.dumps(signals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Stored {len(items)} unique articles from {len(sources)} active sources.")
    print(f"Iran layer: {len(iran_items)} retained articles from {payload['active_iran_sources']} active Iran sources.")
    print(f"Detected {sum(len(i.get('brands', [])) for i in items)} brand mentions in retained articles.")
    for status in source_status:
        print(
            f"- {status['name']}: {status['entries_seen']} seen; "
            f"{status['entries_matched']} matched; bozo={status['bozo']}"
        )


if __name__ == "__main__":
    main()
