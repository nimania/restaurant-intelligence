import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fa_editor import editorialize_report, editorialize_summary, editorialize_title


class PersianEditorialTests(unittest.TestCase):
    def test_translationese_is_simplified_without_losing_numbers(self):
        text = "این شرکت در حال حاضر در تلاش است تا 250 شعبه جدید افتتاح کند."
        edited = editorialize_report(text)
        self.assertIn("۲۵۰" if "۲۵۰" in edited else "250", edited)
        self.assertIn("می‌کوشد", edited)
        self.assertNotIn("در تلاش است تا", edited)

    def test_title_keeps_subject(self):
        title = "این شرکت اعلام کرد که قصد دارد فروشگاه‌های بیشتری باز کند"
        edited = editorialize_title(title)
        self.assertTrue(edited.startswith("این شرکت"))
        self.assertIn("قصد دارد", edited)

    def test_long_sentence_can_be_split_at_safe_connector(self):
        text = (
            "استارباکس برنامه تازه‌ای برای نوسازی فروشگاه‌ها و افزایش سرعت سرویس معرفی کرده است، "
            "اما مدیران شرکت تأکید کرده‌اند که این تغییر نباید تجربه مشتری را تضعیف کند و قرار است "
            "اجرای آن در چند مرحله و در بازارهای مختلف انجام شود."
        )
        edited = editorialize_report(text)
        self.assertIn("اما", edited)
        self.assertGreaterEqual(edited.count("."), 1)

    def test_report_is_paragraphed(self):
        text = "جمله اول درباره خبر است. جمله دوم جزئیات را توضیح می‌دهد. جمله سوم پیامد را بیان می‌کند."
        edited = editorialize_report(text, sentences_per_paragraph=2)
        self.assertIn("\n\n", edited)

    def test_summary_limits_sentence_count(self):
        text = "جمله اول. جمله دوم. جمله سوم. جمله چهارم."
        edited = editorialize_summary(text, max_sentences=2)
        self.assertNotIn("جمله سوم", edited)


if __name__ == "__main__":
    unittest.main()
