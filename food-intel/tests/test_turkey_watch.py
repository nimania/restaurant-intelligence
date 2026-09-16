import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from classify_tr import classify_tr
from entities import detect_brands, load_brands
from translate_fa import source_language


class TurkeyWatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_brands()
        cls.by_id = {x.get("id"): x for x in cls.catalog}

    def test_turkish_catalog_is_loaded(self):
        self.assertIn("tavuk_dunyasi", self.by_id)
        self.assertEqual(self.by_id["tavuk_dunyasi"].get("market"), "turkey")
        self.assertIn("ulker", self.by_id)

    def test_detects_turkish_brand_with_unicode_name(self):
        matches = detect_brands(
            "Tavuk Dünyası yeni şubesini açtı",
            "Restoran zinciri büyüme planını duyurdu.",
            self.catalog,
        )
        ids = {x.get("id") for x in matches}
        self.assertIn("tavuk_dunyasi", ids)
        match = next(x for x in matches if x.get("id") == "tavuk_dunyasi")
        self.assertEqual(match.get("market"), "turkey")

    def test_turkish_ai_restaurant_classification(self):
        categories, topics = classify_tr(
            "Restoranlarda yapay zeka ve otomasyon yatırımı",
            "Yeni teknoloji dijital sipariş ve mutfak operasyonlarında kullanılacak.",
        )
        self.assertIn("restaurant_technology_ai", categories)
        self.assertIn("AI", topics)
        self.assertIn("automation", topics)

    def test_turkish_source_language_normalization(self):
        self.assertEqual(source_language("tr"), "tr")
        self.assertEqual(source_language("tr-TR"), "tr")
        self.assertEqual(source_language("en-US"), "en")


if __name__ == "__main__":
    unittest.main()
