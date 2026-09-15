import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from body_reader import extract_article_text, select_report_source


class BodyReaderTests(unittest.TestCase):
    def test_prefers_jsonld_article_body(self):
        body = " ".join(["Restaurant operators announced a major technology investment with detailed figures."] * 12)
        html = f'''<html><head><script type="application/ld+json">{{"@type":"NewsArticle","articleBody":{body!r}}}</script></head><body><p>menu</p></body></html>'''
        # JSON must use double-quoted strings; build it explicitly for the parser.
        import json
        html = '<script type="application/ld+json">' + json.dumps({"@type": "NewsArticle", "articleBody": body}) + '</script>'
        text, extractor, paragraphs = extract_article_text(html)
        self.assertIn("technology investment", text)
        self.assertEqual(extractor, "jsonld.articleBody")
        self.assertGreaterEqual(paragraphs, 1)

    def test_extracts_article_paragraphs_and_ignores_navigation(self):
        paragraphs = ''.join(f'<p>Paragraph {i} contains meaningful restaurant industry reporting, figures, strategy and operating details for readers.</p>' for i in range(8))
        html = f'<html><nav><p>Subscribe to newsletter</p></nav><article>{paragraphs}</article><footer>footer</footer></html>'
        text, extractor, count = extract_article_text(html)
        self.assertEqual(extractor, "article")
        self.assertGreaterEqual(count, 8)
        self.assertNotIn("Subscribe to newsletter", text)

    def test_report_source_keeps_fact_dense_sentences(self):
        text = (
            "The company announced a new restaurant strategy on Monday. "
            "It will invest $25 million and open 40 locations in 2027. "
            "Management said the plan is expected to reduce operating costs by 12 percent. "
            "A background sentence adds historical context without many facts. "
            "The chain also plans to introduce new kitchen technology across 300 stores. "
            "Executives said the rollout follows a six-month pilot."
        )
        report, selected = select_report_source(text)
        self.assertGreaterEqual(selected, 3)
        self.assertIn("$25 million", report)
        self.assertIn("300 stores", report)
        self.assertLessEqual(len(report), 3200)


if __name__ == "__main__":
    unittest.main()
