import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from fa_polish import prepare_for_translation
from semantic_quality import diagnose_semantics


class TranslationSemanticsTests(unittest.TestCase):
    def test_mars_brand_is_not_planet(self):
        prepared = prepare_for_translation("Mars zeroes in on gut health with startup partnerships")
        self.assertIn("مارس", prepared)
        self.assertIn("focuses on", prepared)
        self.assertNotIn("Mars", prepared)

    def test_bad_mars_translation_is_flagged(self):
        item = {
            "title": "Mars zeroes in on gut health with startup partnerships",
            "summary": "",
            "title_fa": "مریخ سلامت روده را به صفر می‌رساند",
            "summary_fa": "",
            "report_fa": "",
        }
        issues, penalty = diagnose_semantics(item)
        self.assertIn("brand-literal-mars", issues)
        self.assertIn("idiom-literal-zeroes-in", issues)
        self.assertGreaterEqual(penalty, 40)

    def test_business_footprint_is_normalized(self):
        prepared = prepare_for_translation("Brand expands Southern California footprint with a new location")
        self.assertIn("presence", prepared)
        self.assertNotIn("footprint", prepared.lower())

    def test_taps_idiom_is_normalized(self):
        prepared = prepare_for_translation("Arby's taps a TV star to promote Steak Nuggets")
        self.assertIn("selects", prepared)
        self.assertNotIn(" taps ", prepared.lower())


if __name__ == "__main__":
    unittest.main()
