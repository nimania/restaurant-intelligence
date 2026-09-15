from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from dateutil import parser as date_parser

from entities import CATEGORY_FA, TOPIC_FA

CATEGORY_BY_FA = {label: key for key, label in CATEGORY_FA.items()}


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def _window(items: list[dict], start: datetime, end: datetime) -> list[dict]:
    rows = []
    for item in items:
        published = _dt(item.get("published_at"))
        if published and start <= published < end:
            rows.append(item)
    return rows


def _topic_key(topic: str) -> str:
    label = TOPIC_FA.get(topic, topic)
    matching_category = CATEGORY_BY_FA.get(label)
    return matching_category or f"topic:{topic}"


def _topic_keys(item: dict) -> set[str]:
    keys = set(item.get("categories", []))
    keys.update(_topic_key(topic) for topic in item.get("topics", []))
    return keys


def _brand_keys(item: dict) -> set[str]:
    return {b.get("id") for b in item.get("brands", []) if b.get("id")}


def _label_topic(key: str) -> tuple[str, str]:
    if key.startswith("topic:"):
        raw = key.split(":", 1)[1]
        return raw, TOPIC_FA.get(raw, raw)
    return key, CATEGORY_FA.get(key, key)


def _daily_series(items: list[dict], now: datetime, matcher) -> list[int]:
    values = []
    for days_ago in range(6, -1, -1):
        start = (now - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        values.append(sum(1 for item in items if (_dt(item.get("published_at")) and start <= _dt(item.get("published_at")) < end and matcher(item))))
    return values


def _rank(current: Counter, previous: Counter, days_previous: int, labeler, items: list[dict], now: datetime, matcher_factory, limit: int = 10) -> list[dict]:
    rows = []
    for key, count in current.items():
        if count < 2:
            continue
        baseline = previous.get(key, 0) / max(days_previous, 1)
        acceleration = round(count / max(baseline, 0.5), 2)
        raw, fa = labeler(key)
        rows.append({
            "id": raw,
            "label_fa": fa,
            "count_24h": count,
            "previous_daily_avg": round(baseline, 2),
            "acceleration": acceleration,
            "series_7d": _daily_series(items, now, matcher_factory(key)),
        })
    rows.sort(key=lambda x: (x["acceleration"], x["count_24h"]), reverse=True)
    return rows[:limit]


def _category_count(items: list[dict], category: str, start: datetime, end: datetime) -> int:
    return sum(
        1 for item in items
        if (_dt(item.get("published_at")) and start <= _dt(item.get("published_at")) < end and category in (item.get("categories") or []))
    )


def build_signals(items: list[dict], generated_at: str) -> dict:
    now = _dt(generated_at) or datetime.now(timezone.utc)
    last24_start = now - timedelta(days=1)
    last24 = _window(items, last24_start, now + timedelta(seconds=1))
    previous6d = _window(items, now - timedelta(days=7), last24_start)

    topic_now = Counter(k for item in last24 for k in _topic_keys(item))
    topic_prev = Counter(k for item in previous6d for k in _topic_keys(item))
    brand_now = Counter(k for item in last24 for k in _brand_keys(item))
    brand_prev = Counter(k for item in previous6d for k in _brand_keys(item))

    brand_meta = {}
    for item in items:
        for brand in item.get("brands", []):
            brand_meta[brand.get("id")] = brand

    def brand_labeler(key: str) -> tuple[str, str]:
        brand = brand_meta.get(key, {})
        return key, brand.get("fa") or brand.get("name") or key

    topics = _rank(
        topic_now,
        topic_prev,
        6,
        _label_topic,
        items,
        now,
        lambda key: lambda item: key in _topic_keys(item),
    )
    brands = _rank(
        brand_now,
        brand_prev,
        6,
        brand_labeler,
        items,
        now,
        lambda key: lambda item: key in _brand_keys(item),
    )

    focus_categories = [
        "restaurant_technology_ai",
        "equipment_automation",
        "food_cost_pricing",
        "food_safety",
        "restaurant_operations",
        "marketing_branding",
    ]
    dashboard = []
    for category in focus_categories:
        count = _category_count(items, category, last24_start, now + timedelta(seconds=1))
        if not count:
            continue
        dashboard.append({
            "id": category,
            "label_fa": CATEGORY_FA.get(category, category),
            "count_24h": count,
            "series_7d": _daily_series(items, now, lambda item, c=category: c in (item.get("categories") or [])),
        })

    iran_24h = sum(1 for item in last24 if item.get("market") == "iran" or (item.get("iran_relevance_score") or 0) >= 70)
    image_24h = sum(1 for item in last24 if item.get("image_url"))
    dashboard.insert(0, {
        "id": "iran_market",
        "label_fa": "بازار ایران",
        "count_24h": iran_24h,
        "series_7d": _daily_series(items, now, lambda item: item.get("market") == "iran" or (item.get("iran_relevance_score") or 0) >= 70),
    })

    radar_bits = []
    if topics:
        radar_bits.append("موضوع‌های رو به رشد: " + "، ".join(x["label_fa"] for x in topics[:3]))
    if brands:
        radar_bits.append("برندهای پرتکرار: " + "، ".join(x["label_fa"] for x in brands[:3]))

    return {
        "schema_version": "0.5",
        "generated_at": generated_at,
        "articles_24h": len(last24),
        "articles_previous_6d": len(previous6d),
        "images_24h": image_24h,
        "trending_topics": topics,
        "trending_brands": brands,
        "dashboard": dashboard,
        "radar_fa": "؛ ".join(radar_bits) + ("." if radar_bits else ""),
    }
