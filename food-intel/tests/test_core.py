import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classify import classify
from collect import article_id, canonicalize_url, clean_text


class CoreTests(unittest.TestCase):
    def test_canonicalize_url_removes_tracking(self):
        url = "https://Example.com/story/?utm_source=x&id=7&fbclid=abc"
        self.assertEqual(canonicalize_url(url), "https://example.com/story?id=7")

    def test_article_id_is_stable(self):
        first = article_id("https://example.com/a", "Title", "source")
        second = article_id("https://example.com/a", "Different title", "other")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 20)

    def test_clean_text_strips_html(self):
        self.assertEqual(clean_text("<p>Hello&nbsp;world</p>"), "Hello world")

    def test_classifier_matches_multiple_categories(self):
        categories, topics = classify(
            "Restaurant chain adds AI drive-thru ordering",
            "The quick-service operator is testing automation and a new menu.",
        )
        self.assertIn("qsr_fast_food", categories)
        self.assertIn("restaurant_technology_ai", categories)
        self.assertIn("delivery_drive_thru", categories)
        self.assertIn("menu_product_innovation", categories)
        self.assertIn("AI", topics)


if __name__ == "__main__":
    unittest.main()
