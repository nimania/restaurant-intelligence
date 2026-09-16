import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fa_narrative import build_narrative, source_chunks
from translate_fa import _protect_source_terms, _restore_source_terms


class TranslationV2Tests(unittest.TestCase):
    def test_brand_and_terms_are_protected_without_persian_source_mix(self):
        source = "Mars is testing a loyalty program and same-store sales improved."
        protected, mapping = _protect_source_terms(source)
        self.assertNotIn("مارس", protected)
        self.assertNotIn("برنامه وفاداری", protected)
        self.assertIn("NIMATERM", protected)
        restored = _restore_source_terms(protected, mapping)
        self.assertIn("مارس", restored)
        self.assertIn("برنامه وفاداری مشتری", restored)

    def test_source_units_stay_short_and_ordered(self):
        text = "First factual sentence about a restaurant. Second sentence has another fact. Third sentence reports growth."
        units = source_chunks(text)
        self.assertGreaterEqual(len(units), 3)
        self.assertTrue(units[0].startswith("First"))
        self.assertTrue(all(len(x) <= 300 for x in units))

    def test_recap_is_separate_from_full_report(self):
        translated = [
            "شرکت یک شعبه جدید افتتاح کرده است.",
            "این شعبه از فناوری سفارش‌گیری دیجیتال استفاده می‌کند.",
            "مدیریت شرکت گفته است هدف، افزایش سرعت سرویس است.",
            "این طرح ابتدا در چند بازار آزمایش خواهد شد.",
            "شرکت پس از ارزیابی نتایج درباره توسعه بیشتر تصمیم می‌گیرد.",
        ]
        report, recap = build_narrative(translated)
        self.assertTrue(report)
        self.assertTrue(recap)
        self.assertLessEqual(len(recap.split()), 105)
        self.assertIn("شعبه", report)


if __name__ == "__main__":
    unittest.main()
