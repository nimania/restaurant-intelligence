from __future__ import annotations

from datetime import datetime, timezone

CATEGORY_WEIGHTS = {
    "restaurant_operations": 12,
    "restaurant_technology_ai": 12,
    "food_cost_pricing": 12,
    "food_safety": 12,
    "equipment_automation": 10,
    "qsr_fast_food": 9,
    "fast_casual": 8,
    "supply_chain": 9,
    "menu_product_innovation": 8,
    "labor_management": 8,
    "consumer_behavior": 8,
    "food_manufacturing": 8,
    "franchising": 7,
    "delivery_drive_thru": 7,
    "ingredients_rd": 7,
    "regulation": 7,
    "beverage": 6,
    "marketing_branding": 5,
    "retail_food": 5,
    "sustainability": 5,
}

SOURCE_CLASS_BONUS = {
    "regulator": 12,
    "specialist_publication": 8,
    "industry_publication": 7,
    "industry_news": 4,
}


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def relevance_score(article: dict, source: dict | None = None, now: datetime | None = None) -> int:
    """Return a deterministic 0–100 editorial relevance score.

    v0.3 intentionally avoids opaque ML. The score combines source priority,
    source type, topic/category relevance, freshness and metadata quality.
    """
    source = source or {}
    now = now or datetime.now(timezone.utc)

    priority = int(source.get("priority") or article.get("source", {}).get("priority") or 3)
    score = {1: 42, 2: 34, 3: 26}.get(priority, 22)

    source_class = source.get("source_class") or article.get("source", {}).get("class")
    score += SOURCE_CLASS_BONUS.get(source_class, 2)

    categories = article.get("categories") or []
    if categories:
        weights = sorted((CATEGORY_WEIGHTS.get(cat, 3) for cat in categories), reverse=True)
        score += weights[0]
        if len(weights) > 1:
            score += min(5, weights[1] // 2)

    topics = article.get("topics") or []
    score += min(8, len(topics) * 2)

    published = _parse_datetime(article.get("published_at"))
    if published:
        age_hours = max(0.0, (now - published).total_seconds() / 3600)
        if age_hours <= 24:
            score += 15
        elif age_hours <= 72:
            score += 11
        elif age_hours <= 168:
            score += 7
        elif age_hours <= 336:
            score += 3

    title = article.get("title") or ""
    summary = article.get("summary") or ""
    if len(title) >= 25:
        score += 2
    if len(summary) >= 120:
        score += 4

    return max(0, min(100, round(score)))
