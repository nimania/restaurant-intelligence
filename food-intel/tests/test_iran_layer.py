import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classify_fa import classify_fa
from collect import iran_relevance_score, source_accepts_entry
from entities import detect_brands, load_brands


class IranLayerTests(unittest.TestCase):
    def test_iran_registry_has_active_specialist_and_filtered_sources(self):
        payload = yaml.safe_load((ROOT / "config" / "sources_iran.yml").read_text(encoding="utf-8"))
        active = [s for s in payload["sources"] if s.get("enabled")]
        self.assertGreaterEqual(len(active), 6)
        self.assertTrue(any(s.get("source_class") == "specialist_publication" for s in active))
        self.assertTrue(any(s.get("source_class") == "general_news_filtered" for s in active))
        for source in active:
            self.assertEqual(source.get("market"), "iran")
            self.assertTrue(source.get("feed_url", "").startswith("https://"))

    def test_general_source_filter_keeps_food_story(self):
        source = {"include_keywords": ["صنایع غذایی", "رستوران"]}
        entry = SimpleNamespace(title="سرمایه‌گذاری جدید در صنایع غذایی ایران", summary="", description="")
        self.assertTrue(source_accepts_entry(entry, source))

    def test_general_source_filter_rejects_unrelated_story(self):
        source = {"include_keywords": ["صنایع غذایی", "رستوران"]}
        entry = SimpleNamespace(title="نتیجه مسابقه فوتبال", summary="", description="")
        self.assertFalse(source_accepts_entry(entry, source))

    def test_persian_classifier_detects_packaging_and_equipment(self):
        categories, topics = classify_fa(
            "ماشین‌آلات جدید بسته‌بندی برای صنایع غذایی رونمایی شد",
            "خط تولید و تجهیزات آشپزخانه صنعتی نیز معرفی شدند",
        )
        self.assertIn("packaging_design", categories)
        self.assertIn("equipment_automation", categories)
        self.assertIn("packaging", topics)

    def test_iranian_brand_detection_and_score(self):
        brands = detect_brands("کاله خط تولید جدید خود را افتتاح کرد", "", load_brands())
        self.assertTrue(any(b["id"] == "kalleh" for b in brands))
        score = iran_relevance_score(
            "کاله خط تولید جدید خود را افتتاح کرد",
            "خبر مربوط به صنایع غذایی ایران است",
            {"market": "iran", "country": "IR", "language": "fa"},
            brands,
        )
        self.assertGreaterEqual(score, 95)


if __name__ == "__main__":
    unittest.main()
