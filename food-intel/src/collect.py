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
from entities import detect_brands, load_brands
from score import relevance_score
from signals import build_signals

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "config" / "sources.yml"
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


def load_sources() -> list[dict]:
    payload = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8")) or {}
    return [s for s in payload.get("sources", []) if s.get("enabled") and s.get("type") == "rss" and s.get("feed_url")]


def load_existing() -> dict:
    if not DATA_PATH.exists():
        return {"items": []}
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"items": []}


def normalize_entry(entry, source: dict, brand_catalog: list[dict]) -> dict | None:
    title = clean_text(getattr(entry, "title", ""))
    url = canonicalize_url(getattr(entry, "link", "") or "")
    if not title or not url:
        return None

    summary = clean_text(getattr(entry, "summary", "") or getattr(entry, "description", ""))[:1200]
    categories, topics = classify(title, summary, defaults=source.get("default_categories", []))
    published_at = entry_datetime(entry)

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
        },
        "author": clean_text(getattr(entry, "author", "")) or None,
        "published_at": published_at,
        "collected_at": utc_now(),
        "language": source.get("language", "en"),
        "region": source.get("region"),
        "summary": summary,
        "categories": categories,
        "topics": topics,
        "brands": detect_brands(title, summary, brand_catalog),
        "relevance_score": None,
    }
    item["relevance_score"] = relevance_score(item, source)
    return item


def collect_source(source: dict, brand_catalog: list[dict]) -> tuple[list[dict], dict]:
    feed = feedparser.parse(source["feed_url"], agent="FoodIndustryIntelligence/0.4 (+GitHub)")
    status = {
        "source_id": source["id"], "name": source["name"], "feed_url": source["feed_url"],
        "entries_seen": len(feed.entries), "bozo": bool(getattr(feed, "bozo", False)),
    }
    if getattr(feed, "bozo_exception", None):
        status["warning"] = str(feed.bozo_exception)[:300]
    items = []
    for entry in feed.entries:
        item = normalize_entry(entry, source, brand_catalog)
        if item:
            items.append(item)
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

    # Re-enrich the full retained dataset so new entity rules apply immediately.
    for item in by_id.values():
        source = source_by_id.get(item.get("source", {}).get("id"), {})
        item.pop("summary_fa", None)  # Translation is intentionally not stored or published.
        item["brands"] = detect_brands(item.get("title", ""), item.get("summary", ""), brand_catalog)
        item["relevance_score"] = relevance_score(item, source)

    items = sorted(
        by_id.values(),
        key=lambda x: (x.get("published_at") or "", x.get("relevance_score") or 0),
        reverse=True,
    )[:MAX_ITEMS]

    generated_at = utc_now()
    payload = {
        "schema_version": "0.4",
        "generated_at": generated_at,
        "count": len(items),
        "active_sources": len(sources),
        "entries_processed_this_run": processed,
        "source_status": source_status,
        "items": items,
    }
    signals = build_signals(items, generated_at)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SIGNALS_PATH.write_text(json.dumps(signals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Stored {len(items)} unique articles from {len(sources)} active sources.")
    print(f"Detected {sum(len(i.get('brands', [])) for i in items)} brand mentions in retained articles.")
    for status in source_status:
        print(f"- {status['name']}: {status['entries_seen']} entries; bozo={status['bozo']}")


if __name__ == "__main__":
    main()
