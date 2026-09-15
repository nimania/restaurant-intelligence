import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brand_watch import build_watch_sources, watch_matches


class BrandWatchTests(unittest.TestCase):
    def test_specific_restaurant_alias_matches(self):
        watch = {
            "id": "sheila",
            "terms": ["رستوران شیلا", "پیتزا شیلا"],
            "context": ["رستوران", "پیتزا", "شعبه"],
        }
        self.assertTrue(watch_matches("رستوران شیلا شعبه تازه‌ای افتتاح کرد", watch))

    def test_single_word_brand_needs_context(self):
        watch = {
            "id": "kalleh",
            "terms": ["کاله"],
            "context": ["محصول", "برند", "کارخانه", "صادرات"],
        }
        self.assertFalse(watch_matches("سفر به روستای کاله در فصل بهار", watch))
        self.assertTrue(watch_matches("برند کاله محصول تازه‌ای به بازار عرضه کرد", watch))

    def test_sources_are_batched_and_persian_iran_scoped(self):
        watches = [
            {"id": "a", "terms": ["برند الف"]},
            {"id": "b", "terms": ["برند ب"]},
            {"id": "c", "terms": ["برند ج"]},
        ]
        rows = build_watch_sources(watches, {"batch_size": 2, "lookback_days": 14})
        self.assertEqual(len(rows), 2)
        source, batch = rows[0]
        self.assertEqual(len(batch), 2)
        self.assertEqual(source["market"], "iran")
        self.assertIn("news.google.com/rss/search", source["feed_url"])
        self.assertIn("when%3A14d", source["feed_url"])


if __name__ == "__main__":
    unittest.main()
