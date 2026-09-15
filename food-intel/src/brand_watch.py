from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode

import feedparser
import yaml

from collect import DATA_PATH, MAX_ITEMS, SIGNALS_PATH, normalize_entry, utc_now
from entities import load_brands
from signals import build_signals
from translate_fa import apply_persian_translation

ROOT = Path(__file__).resolve().parents[1]
WATCH_PATH = ROOT / "config" / "brand_watch_iran.yml"
GOOGLE_NEWS_SEARCH = "https://news.google.com/rss/search"

FALLBACK_BRANDS = {
    "kabooky": {"id": "kabooky", "name": "Kabooky", "fa": "کابوکی", "market": "iran"},
    "padideh_shandiz": {"id": "padideh_shandiz", "name": "Padideh Shandiz", "fa": "پدیده شاندیز", "market": "iran"},
}


def _norm(value: str | None) -> str:
    return re.sub(
        r"\s+",
        " ",
        (value or "")
        .lower()
        .replace("\u200c", " ")
        .replace("ي", "ی")
        .replace("ك", "ک"),
    ).strip()


def load_watch_config() -> tuple[list[dict], dict]:
    if not WATCH_PATH.exists():
        return [], {}
    payload = yaml.safe_load(WATCH_PATH.read_text(encoding="utf-8")) or {}
    return payload.get("brands", []) or [], payload.get("settings", {}) or {}


def watch_matches(text: str, watch: dict) -> bool:
    """Return True only for reasonably specific brand mentions.

    Multi-word aliases are considered specific enough on their own. Short/single-word
    aliases also need one food/business context term, which reduces false positives
    for names such as «کاله», «میهن» and «فرمند».
    """
    haystack = _norm(text)
    matched_terms = [term for term in watch.get("terms", []) if _norm(term) in haystack]
    if not matched_terms:
        return False
    if any(len(_norm(term).split()) >= 2 for term in matched_terms):
        return True
    contexts = watch.get("context", []) or []
    return not contexts or any(_norm(term) in haystack for term in contexts)


def build_watch_sources(watches: list[dict], settings: dict) -> list[tuple[dict, list[dict]]]:
    try:
        batch_size = max(1, int(settings.get("batch_size", 6)))
    except (TypeError, ValueError):
        batch_size = 6
    try:
        lookback = max(1, int(settings.get("lookback_days", 30)))
    except (TypeError, ValueError):
        lookback = 30
    priority = int(settings.get("priority", 2) or 2)

    rows: list[tuple[dict, list[dict]]] = []
    for index in range(0, len(watches), batch_size):
        batch = watches[index : index + batch_size]
        phrases: list[str] = []
        for watch in batch:
            for term in (watch.get("terms") or [])[:3]:
                clean = str(term).strip()
                if clean and clean not in phrases:
                    phrases.append(clean)
        if not phrases:
            continue
        query = "(" + " OR ".join(f'\"{term}\"' for term in phrases) + f") when:{lookback}d"
        feed_url = GOOGLE_NEWS_SEARCH + "?" + urlencode(
            {"q": query, "hl": "fa", "gl": "IR", "ceid": "IR:fa"}
        )
        n = index // batch_size + 1
        source = {
            "id": f"iran_brand_watch_{n:02d}",
            "name": f"رصد برندهای ایران — دسته {n}",
            "type": "rss",
            "feed_url": feed_url,
            "homepage": "https://news.google.com/",
            "language": "fa",
            "region": "IR",
            "country": "IR",
            "market": "iran",
            "source_class": "brand_watch_search",
            "aggregator": "google_news",
            "default_categories": ["food_industry"],
            "priority": priority,
        }
        rows.append((source, batch))
    return rows


def _brand_meta(brand_id: str, catalog_by_id: dict[str, dict]) -> dict:
    brand = catalog_by_id.get(brand_id) or FALLBACK_BRANDS.get(brand_id) or {
        "id": brand_id,
        "name": brand_id,
        "fa": brand_id,
        "market": "iran",
    }
    return {
        "id": brand["id"],
        "name": brand.get("name") or brand["id"],
        "fa": brand.get("fa") or brand.get("name") or brand["id"],
        "market": "iran",
    }


def _merge_brand_mentions(item: dict, brand_ids: list[str], catalog_by_id: dict[str, dict]) -> None:
    brands = list(item.get("brands") or [])
    existing_ids = {brand.get("id") for brand in brands}
    for brand_id in brand_ids:
        if brand_id not in existing_ids:
            brands.append(_brand_meta(brand_id, catalog_by_id))
            existing_ids.add(brand_id)
    item["brands"] = brands


def main() -> None:
    watches, settings = load_watch_config()
    sources = build_watch_sources(watches, settings)
    if not watches or not sources or not DATA_PATH.exists():
        print("Iran brand watch: nothing to do.")
        return

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing_items = payload.get("items", []) or []
    by_id = {item.get("id"): item for item in existing_items if item.get("id")}
    previous_by_id = dict(by_id)

    catalog = load_brands()
    catalog_by_id = {brand.get("id"): brand for brand in catalog if brand.get("id")}
    new_items: list[dict] = []
    statuses: list[dict] = []
    entries_seen = 0
    entries_matched = 0

    for source, batch in sources:
        feed = feedparser.parse(source["feed_url"], agent="FoodIndustryIntelligence/1.3 (+GitHub)")
        status = {
            "source_id": source["id"],
            "name": source["name"],
            "feed_url": source["feed_url"],
            "market": "iran",
            "aggregator": "google_news",
            "brand_watch": True,
            "entries_seen": len(feed.entries),
            "entries_matched": 0,
            "bozo": bool(getattr(feed, "bozo", False)),
        }
        if getattr(feed, "bozo_exception", None):
            status["warning"] = str(feed.bozo_exception)[:300]
        entries_seen += len(feed.entries)

        for entry in feed.entries:
            title = str(getattr(entry, "title", "") or "")
            summary = str(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
            searchable = f"{title} {summary}"
            matched_ids = [watch["id"] for watch in batch if watch_matches(searchable, watch)]
            if not matched_ids:
                continue
            entries_matched += 1
            status["entries_matched"] += 1

            item = normalize_entry(entry, source, catalog)
            if not item:
                continue
            _merge_brand_mentions(item, matched_ids, catalog_by_id)
            item["market"] = "iran"
            item["iran_relevance_score"] = max(int(item.get("iran_relevance_score") or 0), 95)
            item["relevance_score"] = max(int(item.get("relevance_score") or 0), 70)
            item["brand_watch"] = {
                "mode": "google_news_rss",
                "matched_brand_ids": matched_ids,
                "watch_source_id": source["id"],
            }

            current = by_id.get(item["id"])
            if current:
                _merge_brand_mentions(current, matched_ids, catalog_by_id)
                current["brand_watch"] = item["brand_watch"]
                current["market"] = "iran"
                current["iran_relevance_score"] = max(int(current.get("iran_relevance_score") or 0), 95)
                current["relevance_score"] = max(int(current.get("relevance_score") or 0), 70)
            else:
                by_id[item["id"]] = item
                new_items.append(item)
        statuses.append(status)

    # Brand-watch search is Persian-first, so this mostly normalizes rather than
    # calling an external translator. Body/quality enrichment runs afterwards.
    translation_stats = apply_persian_translation(new_items, previous_by_id)
    for item in new_items:
        item.pop("_report_source", None)

    items = sorted(
        by_id.values(),
        key=lambda x: (x.get("published_at") or "", x.get("relevance_score") or 0),
        reverse=True,
    )[:MAX_ITEMS]
    generated_at = utc_now()
    iran_items = [
        item for item in items
        if item.get("market") == "iran" or (item.get("iran_relevance_score") or 0) >= 70
    ]

    payload["schema_version"] = "0.20"
    payload["generated_at"] = generated_at
    payload["count"] = len(items)
    payload["iran_count"] = len(iran_items)
    payload["active_sources"] = int(payload.get("active_sources") or 0) + len(sources)
    payload["active_iran_sources"] = int(payload.get("active_iran_sources") or 0) + len(sources)
    payload["entries_processed_this_run"] = int(payload.get("entries_processed_this_run") or 0) + entries_matched
    payload["brand_watch_stats"] = {
        "brands_tracked": len(watches),
        "search_feeds": len(sources),
        "entries_seen": entries_seen,
        "entries_matched": entries_matched,
        "new_items": len(new_items),
        "persian_originals": translation_stats.persian_original,
        "translation_failed": translation_stats.failed,
    }
    payload["source_status"] = list(payload.get("source_status") or []) + statuses
    payload["items"] = items

    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SIGNALS_PATH.write_text(
        json.dumps(build_signals(items, generated_at), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        "Iran brand watch: "
        f"{len(watches)} brands; {len(sources)} search feeds; {entries_seen} seen; "
        f"{entries_matched} matched; {len(new_items)} new."
    )


if __name__ == "__main__":
    main()
