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


def _rank(current: Counter, previous: Counter, days_previous: int, labeler, limit: int = 10) -> list[dict]:
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
        })
    rows.sort(key=lambda x: (x["acceleration"], x["count_24h"]), reverse=True)
    return rows[:limit]


def build_signals(items: list[dict], generated_at: str) -> dict:
    now = _dt(generated_at) or datetime.now(timezone.utc)
    last24 = _window(items, now - timedelta(days=1), now + timedelta(seconds=1))
    previous6d = _window(items, now - timedelta(days=7), now - timedelta(days=1))

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

    topics = _rank(topic_now, topic_prev, 6, _label_topic)
    brands = _rank(brand_now, brand_prev, 6, brand_labeler)

    radar_bits = []
    if topics:
        radar_bits.append("موضوع‌های رو به رشد: " + "، ".join(x["label_fa"] for x in topics[:3]))
    if brands:
        radar_bits.append("برندهای پرتکرار: " + "، ".join(x["label_fa"] for x in brands[:3]))

    return {
        "schema_version": "0.4",
        "generated_at": generated_at,
        "articles_24h": len(last24),
        "articles_previous_6d": len(previous6d),
        "trending_topics": topics,
        "trending_brands": brands,
        "radar_fa": "؛ ".join(radar_bits) + ("." if radar_bits else ""),
    }
