import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geo import enrich_geo


class GeoTests(unittest.TestCase):
    def test_detects_iran_city(self):
        geo = enrich_geo("افتتاح کارخانه جدید در نوشهر", "سرمایه‌گذاری در صنعت غذا", {"country": "IR"})
        self.assertEqual(geo["primary_country"]["code"], "IR")
        self.assertIn("nowshahr", [c["id"] for c in geo["cities"]])
        self.assertEqual(geo["confidence"], "high")

    def test_detects_country_from_text(self):
        geo = enrich_geo("Restaurant expansion in Canada", "A major chain opens stores in Toronto", {})
        self.assertEqual(geo["primary_country"]["code"], "CA")
        self.assertEqual(geo["primary_country"]["basis"], "text")

    def test_source_country_is_only_fallback(self):
        geo = enrich_geo("Global packaging trends", "No country is named", {"country": "US"})
        self.assertEqual(geo["primary_country"]["code"], "US")
        self.assertEqual(geo["primary_country"]["basis"], "source")
        self.assertEqual(geo["confidence"], "medium")


if __name__ == "__main__":
    unittest.main()
