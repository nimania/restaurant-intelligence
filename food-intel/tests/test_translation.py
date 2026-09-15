import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from translate_fa import compact, looks_persian


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


if __name__ == "__main__":
    unittest.main()
