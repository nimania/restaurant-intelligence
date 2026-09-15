import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brand_watch import watch_matches
from brand_watch_global import _norm_title, bing_source


class GlobalBrandWatchTests(unittest.TestCase):
    def test_specific_brand_and_context_match(self):
        watch = {"id": "mcdonalds", "terms": ["McDonald's"], "context": ["restaurant", "menu"]}
        self.assertTrue(watch_matches("McDonald's restaurant sales rise after menu launch", watch))

    def test_ambiguous_single_word_needs_context(self):
        watch = {"id": "mars", "terms": ["Mars"], "context": ["food", "snacks"]}
        self.assertFalse(watch_matches("NASA releases new images of Mars", watch))
        self.assertTrue(watch_matches("Mars food group expands snacks portfolio", watch))

    def test_title_normalization_removes_publisher_suffix(self):
        self.assertEqual(_norm_title("McDonald's opens new concept - Reuters"), "mcdonald s opens new concept")

    def test_bing_source_is_world_scoped(self):
        source = bing_source({"id": "starbucks", "terms": ["Starbucks"], "context": ["coffee"]})
        self.assertEqual(source["market"], "world")
        self.assertEqual(source["language"], "en")
        self.assertIn("bing.com/news/search", source["feed_url"])


if __name__ == "__main__":
    unittest.main()
