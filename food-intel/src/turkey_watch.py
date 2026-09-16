from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import feedparser
import yaml

from brand_watch import watch_matches
from classify_tr import classify_tr
from collect import DATA_PATH, MAX_ITEMS, SIGNALS_PATH, merge_unique, normalize_entry, utc_now
from entities import load_brands
from signals import build_signals
from translate_fa import apply_persian_translation

ROOT = Path(__file__).resolve().parents[1]
BRAND_WATCH_PATH = ROOT / "config" / "brand_watch_turkey.yml"
DISCOVERY_PATH = ROOT / "config" / "sources_turkey_discovery.yml"
BING_NEWS = "https://www.bing.com/news/search"
USER_AGENT = "Mozilla/5.0 (compatible; FoodIndustryIntelligence/2.3; +https://github.com/nimania/restaurant-intelligence)"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _norm_title(value: str | None) -> str:
    text = (value or "").lower().replace("’", "'").replace("–", "-")
    text = re.sub(r"\s+-\s+[^-]{2,90}$", "", text)
    text = re.sub(r"[^\w\u0600-\u06ff]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _norm_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").lower()).strip()


def _feed_url(query: str) -> str:
    return BING_NEWS + "?" + urlencode({
        "q": query,
        "format": "rss",
        "setlang": "tr-tr",
        "cc": "TR",
        "qft": 'sortbydate="1"',
    })


def _fetch_feed(url: str):
    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml,application/xml,text/xml,*/*",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.6",
    })
    with urlopen(request, timeout=6) as response:
        body = response.read(1_500_000)
    return feedparser.parse(body)


def _source(source_id: str, name: str, query: str, categories: list[str], source_class: str) -> dict:
    return {
        "id": source_id,
        "name": name,
        "type": "rss",
        "feed_url": _feed_url(query),
        "homepage": "https://www.bing.com/news",
        "language": "tr",
        "region": "TR",
        "country": "TR",
        "market": "turkey",
        "source_class": source_class,
        "aggregator": "bing_news",
        "default_categories": categories or ["food_industry"],
        "priority": 2,
    }


def _brand_source(watch: dict) -> dict:
    terms = [str(x).strip() for x in watch.get("terms", []) if str(x).strip()]
    contexts = [str(x).strip() for x in watch.get("context", []) if str(x).strip()]
    brand_query = " OR ".join(f'\"{x}\"' for x in terms[:3])
    context_query = " OR ".join(f'\"{x}\"' if " " in x else x for x in contexts[:6])
    query = f"({brand_query})"
    if context_query:
        query += f" ({context_query})"
    return _source(
        f"turkey_brand_bing_{watch['id']}",
        f"Türkiye Brand Watch — {watch.get('name') or watch['id']}",
        query,
        ["food_industry"],
        "turkey_brand_watch",
    )


def _brand_meta(brand_id: str, catalog_by_id: dict[str, dict]) -> dict:
    b = catalog_by_id.get(brand_id) or {"id": brand_id, "name": brand_id, "fa": brand_id, "market": "turkey"}
    return {
        "id": b["id"],
        "name": b.get("name") or b["id"],
        "fa": b.get("fa") or b.get("name") or b["id"],
        "market": "turkey",
    }


def _merge_brand(item: dict, brand_id: str, catalog_by_id: dict[str, dict]) -> None:
    brands = list(item.get("brands") or [])
    if brand_id not in {b.get("id") for b in brands}:
        brands.append(_brand_meta(brand_id, catalog_by_id))
    item["brands"] = brands


def _merge_turkish_classification(item: dict) -> None:
    cats, topics = classify_tr(str(item.get("title") or ""), str(item.get("summary") or ""))
    item["categories"] = merge_unique(item.get("categories") or [], cats)[:10]
    item["topics"] = merge_unique(item.get("topics") or [], topics)[:14]


def _include_match(text: str, include: list[str]) -> bool:
    if not include:
        return True
    hay = _norm_text(text)
    return any(_norm_text(term) in hay for term in include)


def main() -> None:
    brand_payload = _load_yaml(BRAND_WATCH_PATH)
    discovery_payload = _load_yaml(DISCOVERY_PATH)
    watches = brand_payload.get("brands", []) or []
    settings = brand_payload.get("settings", {}) or {}
    discovery = discovery_payload.get("queries", []) or []
    if not DATA_PATH.exists():
        print("Turkey watch: news.json does not exist.")
        return

    try:
        brand_limit = max(1, int(settings.get("max_brands_per_run", len(watches) or 1)))
    except (TypeError, ValueError):
        brand_limit = len(watches)
    watches = watches[:brand_limit]

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing = payload.get("items", []) or []
    by_id = {x.get("id"): x for x in existing if x.get("id")}
    previous_by_id = dict(by_id)
    title_index = {_norm_title(x.get("title")): x for x in existing if _norm_title(x.get("title"))}

    catalog = load_brands()
    catalog_by_id = {b.get("id"): b for b in catalog if b.get("id")}
    new_items: list[dict] = []
    statuses: list[dict] = []
    total_seen = total_matched = duplicates = failures = 0
    brand_matched = sector_matched = 0

    jobs: list[tuple[dict, dict | None, list[str]]] = []
    for watch in watches:
        jobs.append((_brand_source(watch), watch, []))
    for row in discovery:
        source = _source(
            f"turkey_discovery_{row['id']}",
            row.get("name") or row["id"],
            str(row.get("query") or ""),
            list(row.get("categories") or ["food_industry"]),
            "turkey_sector_discovery",
        )
        jobs.append((source, None, list(row.get("include") or [])))

    for source, watch, include in jobs:
        status = {
            "source_id": source["id"],
            "name": source["name"],
            "feed_url": source["feed_url"],
            "market": "turkey",
            "country": "TR",
            "aggregator": "bing_news",
            "brand_watch": bool(watch),
            "entries_seen": 0,
            "entries_matched": 0,
            "bozo": False,
        }
        try:
            feed = _fetch_feed(source["feed_url"])
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
            searchable = f"{title} {summary}"
            if watch:
                if not watch_matches(searchable, watch):
                    continue
            elif not _include_match(searchable, include):
                continue

            status["entries_matched"] += 1
            total_matched += 1
            if watch:
                brand_matched += 1
            else:
                sector_matched += 1

            duplicate = title_index.get(_norm_title(title))
            if duplicate:
                duplicate["market"] = duplicate.get("market") or "turkey"
                duplicate["country"] = duplicate.get("country") or "TR"
                if watch:
                    _merge_brand(duplicate, watch["id"], catalog_by_id)
                    duplicate.setdefault("brand_watch", {})
                    ids = list(duplicate["brand_watch"].get("matched_brand_ids") or [])
                    duplicate["brand_watch"].update({
                        "mode": "turkey_bing_news_rss",
                        "matched_brand_ids": sorted(set(ids + [watch["id"]])),
                        "watch_source_id": source["id"],
                    })
                _merge_turkish_classification(duplicate)
                duplicates += 1
                continue

            item = normalize_entry(entry, source, catalog)
            if not item:
                continue
            item["market"] = "turkey"
            item["country"] = "TR"
            item["relevance_score"] = max(int(item.get("relevance_score") or 0), 66 if watch is None else 72)
            _merge_turkish_classification(item)
            if watch:
                _merge_brand(item, watch["id"], catalog_by_id)
                item["brand_watch"] = {
                    "mode": "turkey_bing_news_rss",
                    "matched_brand_ids": [watch["id"]],
                    "watch_source_id": source["id"],
                }
            else:
                item["turkey_discovery"] = {"source_id": source["id"], "query_name": source["name"]}

            current = by_id.get(item["id"])
            if current:
                duplicates += 1
                if watch:
                    _merge_brand(current, watch["id"], catalog_by_id)
            else:
                by_id[item["id"]] = item
                title_index[_norm_title(item.get("title"))] = item
                new_items.append(item)
        statuses.append(status)

    translation_stats = apply_persian_translation(new_items, previous_by_id)
    for item in new_items:
        item.pop("_report_source", None)

    items = sorted(by_id.values(), key=lambda x: (x.get("published_at") or "", x.get("relevance_score") or 0), reverse=True)[:MAX_ITEMS]
    generated_at = utc_now()
    payload["schema_version"] = "0.24"
    payload["generated_at"] = generated_at
    payload["count"] = len(items)
    payload["turkey_watch_stats"] = {
        "brands_tracked": len(watches),
        "sector_queries": len(discovery),
        "provider": "bing_news_rss",
        "entries_seen": total_seen,
        "entries_matched": total_matched,
        "brand_entries_matched": brand_matched,
        "sector_entries_matched": sector_matched,
        "new_items": len(new_items),
        "duplicates_merged": duplicates,
        "failed_feeds": failures,
        "translated": translation_stats.translated,
        "translation_failed": translation_stats.failed,
    }
    payload["source_status"] = list(payload.get("source_status") or []) + statuses
    payload["items"] = items

    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SIGNALS_PATH.write_text(json.dumps(build_signals(items, generated_at), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Turkey watch: "
        f"{len(watches)} brands + {len(discovery)} sector queries; {total_seen} seen; "
        f"{total_matched} matched; {len(new_items)} new; {duplicates} duplicates; {failures} failures."
    )


if __name__ == "__main__":
    main()
