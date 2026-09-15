from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request, urlopen

import yaml
from bs4 import BeautifulSoup

from brand_watch import _brand_meta, _merge_brand_mentions, _norm
from collect import DATA_PATH, MAX_ITEMS, SIGNALS_PATH, normalize_entry, utc_now
from entities import load_brands
from signals import build_signals
from translate_fa import apply_persian_translation

ROOT = Path(__file__).resolve().parents[1]
CHANNELS_PATH = ROOT / "config" / "official_brand_channels_iran.yml"
USER_AGENT = "FoodIndustryIntelligence/1.4 (+https://github.com/nimania/restaurant-intelligence)"


def load_channels() -> tuple[list[dict], dict]:
    if not CHANNELS_PATH.exists():
        return [], {}
    payload = yaml.safe_load(CHANNELS_PATH.read_text(encoding="utf-8")) or {}
    return payload.get("channels", []) or [], payload.get("settings", {}) or {}


def _message_relevant(text: str, channel: dict, settings: dict) -> bool:
    haystack = _norm(text)
    contexts = channel.get("context", []) or []
    if contexts and not any(_norm(term) in haystack for term in contexts):
        return False
    signals = settings.get("signal_terms", []) or []
    if not signals:
        return True
    return any(_norm(term) in haystack for term in signals)


def _headline(text: str) -> str:
    value = re.sub(r"\s+", " ", text or "").strip()
    if not value:
        return ""
    for sep in (". ", "؟ ", "! ", "؛ ", "\n"):
        if sep in value:
            first = value.split(sep, 1)[0].strip()
            if len(first) >= 20:
                value = first
                break
    return value[:180].rstrip("،؛,:-. ")


def fetch_telegram_messages(channel: dict, max_messages: int) -> tuple[list[dict], dict]:
    handle = str(channel.get("telegram") or "").strip().lstrip("@")
    status = {
        "source_id": f"official_telegram_{channel.get('id')}",
        "name": f"{channel.get('fa') or channel.get('id')} — تلگرام رسمی",
        "homepage": f"https://t.me/{handle}" if handle else None,
        "market": "iran",
        "official_brand_channel": True,
        "entries_seen": 0,
        "entries_matched": 0,
        "bozo": False,
    }
    if not handle:
        return [], status

    request = Request(
        f"https://t.me/s/{handle}",
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
    )
    try:
        with urlopen(request, timeout=8) as response:
            html = response.read(1_500_000).decode("utf-8", errors="replace")
    except Exception as exc:
        status["bozo"] = True
        status["warning"] = str(exc)[:300]
        return [], status

    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []
    wraps = soup.select(".tgme_widget_message_wrap")[-max_messages:]
    status["entries_seen"] = len(wraps)
    for wrap in wraps:
        message = wrap.select_one(".tgme_widget_message")
        text_el = wrap.select_one(".tgme_widget_message_text")
        time_el = wrap.select_one("time[datetime]")
        if not message or not text_el:
            continue
        post = str(message.get("data-post") or "").strip()
        text = text_el.get_text(" ", strip=True)
        if not post or len(text) < 20:
            continue
        rows.append(
            {
                "post": post,
                "text": text,
                "published": str(time_el.get("datetime") or "") if time_el else "",
            }
        )
    return rows, status


def main() -> None:
    channels, settings = load_channels()
    if not channels or not DATA_PATH.exists():
        print("Official Iran brand watch: nothing to do.")
        return

    try:
        max_messages = max(5, int(settings.get("max_messages_per_channel", 24)))
    except (TypeError, ValueError):
        max_messages = 24

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing_items = payload.get("items", []) or []
    by_id = {item.get("id"): item for item in existing_items if item.get("id")}
    previous_by_id = dict(by_id)
    catalog = load_brands()
    catalog_by_id = {brand.get("id"): brand for brand in catalog if brand.get("id")}

    new_items: list[dict] = []
    statuses: list[dict] = []
    seen = matched = 0

    for channel in channels:
        messages, status = fetch_telegram_messages(channel, max_messages)
        seen += status.get("entries_seen", 0)
        brand_id = channel.get("id")
        brand_meta = _brand_meta(brand_id, catalog_by_id)
        if channel.get("name"):
            brand_meta["name"] = channel["name"]
        if channel.get("fa"):
            brand_meta["fa"] = channel["fa"]

        source = {
            "id": status["source_id"],
            "name": status["name"],
            "homepage": status.get("homepage"),
            "language": "fa",
            "region": "IR",
            "country": "IR",
            "market": "iran",
            "source_class": "official_brand_social",
            "priority": 1,
            "default_categories": channel.get("categories") or ["food_industry"],
            "aggregator": None,
        }

        for row in messages:
            if not _message_relevant(row["text"], channel, settings):
                continue
            status["entries_matched"] += 1
            matched += 1
            title = _headline(row["text"])
            if not title:
                continue
            entry = SimpleNamespace(
                title=title,
                link=f"https://t.me/{row['post']}",
                summary=row["text"],
                published=row.get("published") or utc_now(),
                author=brand_meta.get("fa") or brand_meta.get("name"),
            )
            item = normalize_entry(entry, source, catalog)
            if not item:
                continue
            _merge_brand_mentions(item, [brand_id], catalog_by_id)
            # Replace fallback display metadata for brands not yet in brands_iran.yml.
            for brand in item.get("brands", []):
                if brand.get("id") == brand_id:
                    brand.update(brand_meta)
            item["market"] = "iran"
            item["iran_relevance_score"] = 100
            item["relevance_score"] = max(int(item.get("relevance_score") or 0), 78)
            item["brand_watch"] = {
                "mode": "official_telegram",
                "matched_brand_ids": [brand_id],
                "watch_source_id": source["id"],
                "official": True,
            }

            current = by_id.get(item["id"])
            if current:
                _merge_brand_mentions(current, [brand_id], catalog_by_id)
                current["brand_watch"] = item["brand_watch"]
                current["market"] = "iran"
                current["iran_relevance_score"] = 100
                current["relevance_score"] = max(int(current.get("relevance_score") or 0), 78)
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

    payload["schema_version"] = "0.20.1"
    payload["generated_at"] = generated_at
    payload["count"] = len(items)
    payload["iran_count"] = len(iran_items)
    payload["active_sources"] = int(payload.get("active_sources") or 0) + len(channels)
    payload["active_iran_sources"] = int(payload.get("active_iran_sources") or 0) + len(channels)
    payload["entries_processed_this_run"] = int(payload.get("entries_processed_this_run") or 0) + matched
    payload["official_brand_watch_stats"] = {
        "channels_tracked": len(channels),
        "messages_seen": seen,
        "messages_matched": matched,
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
        "Official Iran brand watch: "
        f"{len(channels)} channels; {seen} messages seen; {matched} matched; "
        f"{len(new_items)} new."
    )


if __name__ == "__main__":
    main()
