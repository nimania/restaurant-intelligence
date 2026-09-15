from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import feedparser
import yaml

from brand_watch import watch_matches
from collect import DATA_PATH, MAX_ITEMS, SIGNALS_PATH, normalize_entry, utc_now
from entities import load_brands
from signals import build_signals
from translate_fa import apply_persian_translation

ROOT = Path(__file__).resolve().parents[1]
WATCH_PATH = ROOT / "config" / "brand_watch_global.yml"
BING_NEWS = "https://www.bing.com/news/search"
USER_AGENT = "Mozilla/5.0 (compatible; FoodIndustryIntelligence/2.1; +https://github.com/nimania/restaurant-intelligence)"


def load_watch_config() -> tuple[list[dict], dict]:
    if not WATCH_PATH.exists():
        return [], {}
    payload = yaml.safe_load(WATCH_PATH.read_text(encoding="utf-8")) or {}
    return payload.get("brands", []) or [], payload.get("settings", {}) or {}


def _brand_meta(brand_id: str, catalog_by_id: dict[str, dict]) -> dict:
    brand = catalog_by_id.get(brand_id) or {"id": brand_id, "name": brand_id, "fa": brand_id}
    out = {
        "id": brand["id"],
        "name": brand.get("name") or brand["id"],
        "fa": brand.get("fa") or brand.get("name") or brand["id"],
    }
    if brand.get("market"):
        out["market"] = brand.get("market")
    return out


def _merge_brand_mentions(item: dict, brand_ids: list[str], catalog_by_id: dict[str, dict]) -> None:
    brands = list(item.get("brands") or [])
    existing = {brand.get("id") for brand in brands}
    for brand_id in brand_ids:
        if brand_id not in existing:
            brands.append(_brand_meta(brand_id, catalog_by_id))
            existing.add(brand_id)
    item["brands"] = brands


def _norm_title(value: str | None) -> str:
    text = (value or "").lower().replace("’", "'").replace("–", "-")
    text = re.sub(r"\s+-\s+[^-]{2,70}$", "", text)
    text = re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def bing_source(watch: dict) -> dict:
    terms = [str(x).strip() for x in watch.get("terms", []) if str(x).strip()]
    contexts = [str(x).strip() for x in watch.get("context", []) if str(x).strip()]
    brand_query = " OR ".join(f'\"{term}\"' for term in terms[:3])
    context_query = " OR ".join(contexts[:5])
    query = f"({brand_query})"
    if context_query:
        query += f" ({context_query})"
    feed_url = BING_NEWS + "?" + urlencode(
        {
            "q": query,
            "format": "rss",
            "setlang": "en-us",
            "qft": 'sortbydate="1"',
        }
    )
    brand_id = watch["id"]
    return {
        "id": f"global_brand_bing_{brand_id}",
        "name": f"Global Brand Watch — {watch.get('name') or brand_id}",
        "type": "rss",
        "feed_url": feed_url,
        "homepage": "https://www.bing.com/news",
        "language": "en",
        "region": "GLOBAL",
        "market": "world",
        "source_class": "brand_watch_search",
        "aggregator": "bing_news",
        "default_categories": ["food_industry"],
        "priority": 2,
    }


def fetch_feed(url: str):
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml,application/xml,text/xml,*/*"},
    )
    with urlopen(request, timeout=5) as response:
        body = response.read(1_500_000)
    return feedparser.parse(body)


def main() -> None:
    watches, settings = load_watch_config()
    try:
        limit = max(1, int(settings.get("max_brands_per_run", len(watches) or 1)))
    except (TypeError, ValueError):
        limit = len(watches)
    watches = watches[:limit]
    if not watches or not DATA_PATH.exists():
        print("Global brand watch: nothing to do.")
        return

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing_items = payload.get("items", []) or []
    by_id = {item.get("id"): item for item in existing_items if item.get("id")}
    previous_by_id = dict(by_id)
    title_index = {_norm_title(item.get("title")): item for item in existing_items if _norm_title(item.get("title"))}

    catalog = load_brands()
    catalog_by_id = {brand.get("id"): brand for brand in catalog if brand.get("id")}
    new_items: list[dict] = []
    statuses: list[dict] = []
    total_seen = total_matched = failures = duplicates = 0

    for watch in watches:
        source = bing_source(watch)
        brand_id = watch["id"]
        status = {
            "source_id": source["id"],
            "name": source["name"],
            "feed_url": source["feed_url"],
            "market": "world",
            "aggregator": "bing_news",
            "brand_watch": True,
            "entries_seen": 0,
            "entries_matched": 0,
            "bozo": False,
        }
        try:
            feed = fetch_feed(source["feed_url"])
        except Exception as exc:
            failures += 1
            status["bozo"] = True
            status["warning"] = str(exc)[:300]
            statuses.append(status)
            continue

        status["entries_seen"] = len(feed.entries)
        total_seen += len(feed.entries)
        for entry in feed.entries:
            title = str(getattr(entry, "title", "") or "")
            summary = str(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
            if not watch_matches(f"{title} {summary}", watch):
                continue
            status["entries_matched"] += 1
            total_matched += 1

            duplicate = title_index.get(_norm_title(title))
            if duplicate:
                _merge_brand_mentions(duplicate, [brand_id], catalog_by_id)
                duplicate.setdefault("brand_watch", {})
                duplicate["brand_watch"].update({
                    "mode": "global_bing_news_rss",
                    "matched_brand_ids": sorted(set((duplicate["brand_watch"].get("matched_brand_ids") or []) + [brand_id])),
                    "watch_source_id": source["id"],
                })
                duplicates += 1
                continue

            item = normalize_entry(entry, source, catalog)
            if not item:
                continue
            _merge_brand_mentions(item, [brand_id], catalog_by_id)
            if int(item.get("iran_relevance_score") or 0) < 70:
                item["market"] = "world"
            item["relevance_score"] = max(int(item.get("relevance_score") or 0), 72)
            item["brand_watch"] = {
                "mode": "global_bing_news_rss",
                "matched_brand_ids": [brand_id],
                "watch_source_id": source["id"],
            }

            current = by_id.get(item["id"])
            if current:
                _merge_brand_mentions(current, [brand_id], catalog_by_id)
                current["brand_watch"] = item["brand_watch"]
                current["relevance_score"] = max(int(current.get("relevance_score") or 0), 72)
                duplicates += 1
            else:
                by_id[item["id"]] = item
                title_index[_norm_title(item.get("title"))] = item
                new_items.append(item)
        statuses.append(status)

    translation_stats = apply_persian_translation(new_items, previous_by_id)
    for item in new_items:
        item.pop("_report_source", None)

    items = sorted(
        by_id.values(),
        key=lambda x: (x.get("published_at") or "", x.get("relevance_score") or 0),
        reverse=True,
    )[:MAX_ITEMS]
    generated_at = utc_now()

    payload["schema_version"] = "0.21"
    payload["generated_at"] = generated_at
    payload["count"] = len(items)
    payload["entries_processed_this_run"] = int(payload.get("entries_processed_this_run") or 0) + total_matched
    payload["global_brand_watch_stats"] = {
        "brands_tracked": len(watches),
        "provider": "bing_news_rss",
        "entries_seen": total_seen,
        "entries_matched": total_matched,
        "new_items": len(new_items),
        "duplicates_merged": duplicates,
        "failed_feeds": failures,
        "translated": translation_stats.translated,
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
        "Global brand watch: "
        f"{len(watches)} brands; {total_seen} seen; {total_matched} matched; "
        f"{len(new_items)} new; {duplicates} duplicates merged; {failures} feed failures."
    )


if __name__ == "__main__":
    main()
