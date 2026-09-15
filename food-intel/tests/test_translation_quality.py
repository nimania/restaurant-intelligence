import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quality_enrich import _quarantine
from translation_quality import assess_item, assess_text


class TranslationQualityTests(unittest.TestCase):
    def test_clear_persian_news_passes(self):
        q = assess_text(
            "استارباکس اعلام کرد برنامه تازه‌ای برای کاهش زمان انتظار مشتریان در شعب پرتردد اجرا می‌کند.",
            kind="summary",
        )
        self.assertIn(q.status, {"pass", "warn"})
        self.assertGreaterEqual(q.score, 68)

    def test_mostly_english_translation_is_blocked_or_retry(self):
        q = assess_text(
            "Starbucks announced a new operational strategy and digital ordering rollout across stores.",
            kind="summary",
        )
        self.assertIn(q.status, {"retry", "block"})
        self.assertIn("mostly-latin", q.issues)

    def test_very_long_sentence_is_flagged(self):
        text = "این شرکت اعلام کرد " + ("برنامه تازه‌ای برای عملیات رستوران و بهبود تجربه مشتری اجرا می‌کند و " * 12) + "نتایج را بررسی خواهد کرد."
        q = assess_text(text, kind="summary")
        self.assertTrue(any(x in q.issues for x in {"long-sentence", "very-long-sentence", "repetition"}))

    def test_item_quality_uses_title_summary_and_report(self):
        item = {
            "language": "en",
            "translation": {"status": "translated"},
            "title_fa": "مک‌دونالدز طرح تازه‌ای برای سفارش‌گیری دیجیتال آزمایش می‌کند",
            "summary_fa": "این شرکت می‌گوید آزمایش تازه در چند بازار انجام می‌شود و هدف آن کاهش زمان انتظار مشتریان است.",
            "report_fa": "مک‌دونالدز این طرح را در چند بازار آزمایش می‌کند. شرکت هدف اصلی را کاهش زمان انتظار و ساده‌تر شدن فرایند سفارش اعلام کرده است.",
        }
        q = assess_item(item)
        self.assertTrue(q["publishable"])
        self.assertGreaterEqual(q["score"], 68)

    def test_quarantine_preserves_failed_attempt_but_hides_public_fields(self):
        item = {
            "title_fa": "ترجمه مشکل‌دار",
            "summary_fa": "خلاصه مشکل‌دار",
            "report_fa": "گزارش مشکل‌دار",
            "translation": {"status": "translated"},
            "translation_quality": {"status": "retry", "score": 40, "publishable": False},
        }
        _quarantine(item)
        self.assertEqual(item["title_fa"], "")
        self.assertEqual(item["summary_fa"], "")
        self.assertIn("ترجمه مشکل‌دار", item["translation_quarantine"]["title_fa"])
        self.assertEqual(item["translation"]["status"], "quality-quarantined")


if __name__ == "__main__":
    unittest.main()
