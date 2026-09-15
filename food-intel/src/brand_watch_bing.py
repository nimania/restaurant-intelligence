from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import feedparser

from brand_watch import _brand_meta, _merge_brand_mentions, load_watch_config, watch_matches
from collect import DATA_PATH, MAX_ITEMS, SIGNALS_PATH, normalize_entry, utc_now
from entities import load_brands
from signals import build_signals
from translate_fa import apply_persian_translation

BING_NEWS = "https://www.bing.com/news/search"
USER_AGENT = "Mozilla/5.0 (compatible; FoodIndustryIntelligence/1.5; +https://github.com/nimania/restaurant-intelligence)"


def bing_source(watch: dict) -> dict:
    terms = [str(x).strip() for x in watch.get("terms", []) if str(x).strip()]
    query = " OR ".join(f'\"{term}\"' for term in terms[:4])
    feed_url = BING_NEWS + "?" + urlencode(
        {
            "q": query,
            "format": "rss",
            "setlang": "fa",
            "qft": 'sortbydate="1"',
        }
    )
    brand_id = watch["id"]
    return {
        "id": f"iran_brand_bing_{brand_id}",
        "name": f"رصد وب برند — {watch.get('fa') or brand_id}",
        "type": "rss",
        "feed_url": feed_url,
        "homepage": "https://www.bing.com/news",
        "language": "fa",
        "region": "IR",
        "country": "IR",
        "market": "iran",
        "source_class": "brand_watch_search",
        "aggregator": "bing_news",
        "default_categories": ["food_industry"],
        "priority": 2,
    }


def fetch_feed(url: str):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml,application/xml,text/xml,*/*"})
    with urlopen(request, timeout=7) as response:
        body = response.read(1_500_000)
    return feedparser.parse(body)


def main() -> None:
    watches, _settings = load_watch_config()
    if not watches or not DATA_PATH.exists():
        print("Bing Iran brand watch: nothing to do.")
        return

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing_items = payload.get("items", []) or []
    by_id = {item.get("id"): item for item in existing_items if item.get("id")}
    previous_by_id = dict(by_id)
    catalog = load_brands()
    catalog_by_id = {brand.get("id"): brand for brand in catalog if brand.get("id")}

    new_items: list[dict] = []
    statuses: list[dict] = []
    total_seen = total_matched = failures = 0

    for watch in watches:
        source = bing_source(watch)
        status = {
            "source_id": source["id"],
            "name": source["name"],
            "feed_url": source["feed_url"],
            "market": "iran",
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
        brand_id = watch["id"]
        for entry in feed.entries:
            title = str(getattr(entry, "title", "") or "")
            summary = str(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
            if not watch_matches(f"{title} {summary}", watch):
                continue
            status["entries_matched"] += 1
            total_matched += 1
            item = normalize_entry(entry, source, catalog)
            if not item:
                continue
            _merge_brand_mentions(item, [brand_id], catalog_by_id)
            item["market"] = "iran"
            item["iran_relevance_score"] = max(int(item.get("iran_relevance_score") or 0), 95)
            item["relevance_score"] = max(int(item.get("relevance_score") or 0), 72)
            item["brand_watch"] = {
                "mode": "bing_news_rss",
                "matched_brand_ids": [brand_id],
                "watch_source_id": source["id"],
            }

            current = by_id.get(item["id"])
            if current:
                _merge_brand_mentions(current, [brand_id], catalog_by_id)
                current["brand_watch"] = item["brand_watch"]
                current["market"] = "iran"
                current["iran_relevance_score"] = max(int(current.get("iran_relevance_score") or 0), 95)
                current["relevance_score"] = max(int(current.get("relevance_score") or 0), 72)
            else:
                by_id[item["id"]] = item
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
    iran_items = [
        item for item in items
        if item.get("market") == "iran" or (item.get("iran_relevance_score") or 0) >= 70
    ]

    payload["schema_version"] = "0.20.2"
    payload["generated_at"] = generated_at
    payload["count"] = len(items)
    payload["iran_count"] = len(iran_items)
    payload["entries_processed_this_run"] = int(payload.get("entries_processed_this_run") or 0) + total_matched
    payload["brand_web_watch_stats"] = {
        "brands_queried": len(watches),
        "provider": "bing_news_rss",
        "entries_seen": total_seen,
        "entries_matched": total_matched,
        "new_items": len(new_items),
        "failed_feeds": failures,
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
        "Bing Iran brand watch: "
        f"{len(watches)} brands; {total_seen} seen; {total_matched} matched; "
        f"{len(new_items)} new; {failures} feed failures."
    )


if __name__ == "__main__":
    main()
