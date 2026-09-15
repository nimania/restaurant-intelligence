import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fa_narrative import build_narrative, source_chunks
from translate_fa import restore_deep_enrichment


class PersianNarrativeTests(unittest.TestCase):
    def test_source_chunks_are_short_and_ordered(self):
        source = (
            "First sentence contains the lead and the company name. "
            "Second sentence contains 250 locations and a timeline. "
            "Third sentence explains the strategy behind the move. "
            "Fourth sentence adds another operational detail."
        )
        chunks = source_chunks(source)
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(len(x) <= 430 for x in chunks))
        self.assertTrue(chunks[0].startswith("First sentence"))

    def test_narrative_deduplicates_and_paragraphs(self):
        parts = [
            "شرکت اعلام کرد ۲۵۰ شعبه جدید راه‌اندازی می‌کند. شرکت اعلام کرد ۲۵۰ شعبه جدید راه‌اندازی می‌کند.",
            "اجرای برنامه از سال آینده آغاز می‌شود. این شرکت می‌گوید هدف، افزایش سرعت سرویس و کاهش هزینه است.",
            "مدیران شرکت گفته‌اند سرمایه‌گذاری در چند مرحله انجام خواهد شد."
        ]
        narrative, summary = build_narrative(parts, title_fa="برنامه تازه شرکت برای توسعه شعب")
        self.assertEqual(narrative.count("۲۵۰ شعبه"), 1)
        self.assertIn("\n\n", narrative)
        self.assertIn("سال آینده", summary)
        self.assertLessEqual(len(narrative.replace("\n", " ").split()), 230)

    def test_deep_enrichment_survives_feed_refresh(self):
        item = {}
        previous = {
            "narrative_fa": "روایت تفصیلی فارسی",
            "narrative_version": 1,
            "article_body": {"status": "extracted"},
            "report_source_kind": "article_body",
        }
        restore_deep_enrichment(item, previous)
        self.assertEqual(item["narrative_fa"], "روایت تفصیلی فارسی")
        self.assertEqual(item["article_body"]["status"], "extracted")


if __name__ == "__main__":
    unittest.main()
