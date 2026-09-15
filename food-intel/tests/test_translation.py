import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from translate_fa import PersianTranslator, apply_persian_translation, compact, looks_persian


class TranslationTests(unittest.TestCase):
    def test_detects_persian_text(self):
        self.assertTrue(looks_persian("این یک خبر درباره صنعت غذا است"))
        self.assertFalse(looks_persian("Restaurant technology is changing fast"))

    def test_compact_limits_excerpt(self):
        text = "word " * 200
        result = compact(text, 120)
        self.assertLessEqual(len(result), 121)
        self.assertTrue(result.endswith("…"))

    def test_empty_text(self):
        self.assertEqual(compact("", 100), "")

    def test_google_response_parser(self):
        translator = PersianTranslator(pause=0)
        translator._read_json = lambda url: [
            [["فناوری رستوران به سرعت در حال تغییر است", "Restaurant technology is changing fast", None, None]],
            None,
            "en",
        ]
        self.assertEqual(
            translator._google("Restaurant technology is changing fast"),
            "فناوری رستوران به سرعت در حال تغییر است",
        )

    def test_reuses_cached_translation_without_network(self):
        item = {
            "id": "a1",
            "title": "Restaurant technology is changing fast",
            "summary": "A short summary.",
            "language": "en",
            "relevance_score": 90,
            "published_at": "2026-09-15T10:00:00Z",
        }
        previous = {
            "a1": {
                **item,
                "title_fa": "فناوری رستوران به سرعت در حال تغییر است",
                "summary_fa": "یک خلاصه کوتاه.",
                "translation": {"status": "translated", "engine": "http-en-fa"},
            }
        }
        with patch.object(PersianTranslator, "translate_article", side_effect=AssertionError("network should not be used")):
            stats = apply_persian_translation([item], previous)
        self.assertEqual(stats.reused, 1)
        self.assertEqual(item["title_fa"], "فناوری رستوران به سرعت در حال تغییر است")

    def test_translation_limit_queues_remaining_items(self):
        items = [
            {
                "id": f"a{i}",
                "title": f"Restaurant news {i}",
                "summary": "Summary",
                "language": "en",
                "relevance_score": 100 - i,
                "published_at": f"2026-09-15T0{i}:00:00Z",
            }
            for i in range(3)
        ]
        with patch.dict(os.environ, {"FOOD_INTEL_TRANSLATION_LIMIT": "1"}), patch.object(
            PersianTranslator,
            "translate_article",
            return_value=("خبر فارسی", "خلاصه فارسی"),
        ):
            stats = apply_persian_translation(items, {})
        self.assertEqual(stats.translated, 1)
        self.assertEqual(stats.queued, 2)
        self.assertEqual(sum(1 for x in items if x.get("title_fa")), 1)
        self.assertEqual(sum(1 for x in items if x.get("translation", {}).get("status") == "queued"), 2)

    def test_persian_original_never_calls_translator(self):
        item = {
            "id": "fa1",
            "title": "خبر صنعت غذا در ایران",
            "summary": "خلاصه فارسی خبر",
            "language": "fa",
            "relevance_score": 80,
            "published_at": "2026-09-15T10:00:00Z",
        }
        with patch.object(PersianTranslator, "translate_article", side_effect=AssertionError("translator should not run")):
            stats = apply_persian_translation([item], {})
        self.assertEqual(stats.persian_original, 1)
        self.assertEqual(item["title_fa"], item["title"])


if __name__ == "__main__":
    unittest.main()
