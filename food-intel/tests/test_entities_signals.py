import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from entities import detect_brands
from signals import build_signals


class EntitySignalTests(unittest.TestCase):
    def test_detects_known_brand(self):
        catalog = [
            {"id": "mcdonalds", "name": "McDonald's", "fa": "مک‌دونالدز", "aliases": ["mcdonald's", "mcdonalds"]}
        ]
        brands = detect_brands("McDonald's tests a new kitchen system", "", catalog)
        self.assertEqual(brands[0]["id"], "mcdonalds")
        self.assertEqual(brands[0]["fa"], "مک‌دونالدز")

    def test_detects_common_public_alias(self):
        catalog = [
            {"id": "pepsico", "name": "PepsiCo", "fa": "پپسی‌کو", "aliases": ["pepsico"]}
        ]
        brands = detect_brands("Pepsi launches a new restaurant beverage program", "", catalog)
        self.assertEqual(brands[0]["id"], "pepsico")

    def test_does_not_translate_article_text(self):
        catalog = [
            {"id": "starbucks", "name": "Starbucks", "fa": "استارباکس", "aliases": ["starbucks"]}
        ]
        title = "Starbucks updates its store format"
        brands = detect_brands(title, "", catalog)
        self.assertEqual(title, "Starbucks updates its store format")
        self.assertEqual(brands[0]["name"], "Starbucks")

    def test_builds_trending_topic_from_counts(self):
        items = [
            {
                "published_at": "2026-09-15T10:00:00Z",
                "categories": ["restaurant_technology_ai"],
                "topics": ["AI"],
                "brands": [],
            },
            {
                "published_at": "2026-09-15T09:00:00Z",
                "categories": ["restaurant_technology_ai"],
                "topics": ["AI"],
                "brands": [],
            },
            {
                "published_at": "2026-09-12T09:00:00Z",
                "categories": ["food_safety"],
                "topics": ["food safety"],
                "brands": [],
            },
        ]
        signals = build_signals(items, "2026-09-15T11:00:00Z")
        ids = [x["id"] for x in signals["trending_topics"]]
        self.assertIn("restaurant_technology_ai", ids)
        self.assertIn("هوش مصنوعی", signals["radar_fa"])
        row = next(x for x in signals["trending_topics"] if x["id"] == "restaurant_technology_ai")
        self.assertEqual(len(row["series_7d"]), 7)
        dashboard_ids = [x["id"] for x in signals["dashboard"]]
        self.assertIn("restaurant_technology_ai", dashboard_ids)

    def test_overlapping_category_and_topic_are_counted_once(self):
        items = [
            {
                "published_at": "2026-09-15T10:00:00Z",
                "categories": ["beverage"],
                "topics": ["beverage"],
                "brands": [],
            },
            {
                "published_at": "2026-09-15T09:00:00Z",
                "categories": ["beverage"],
                "topics": ["beverage"],
                "brands": [],
            },
        ]
        signals = build_signals(items, "2026-09-15T11:00:00Z")
        beverage_rows = [x for x in signals["trending_topics"] if x["label_fa"] == "نوشیدنی"]
        self.assertEqual(len(beverage_rows), 1)
        self.assertEqual(beverage_rows[0]["count_24h"], 2)


if __name__ == "__main__":
    unittest.main()
