import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from fa_polish import polish_persian, prepare_for_translation  # noqa: E402


class PersianPolishTests(unittest.TestCase):
    def test_brand_names_are_persianized_before_translation(self):
        value = prepare_for_translation("Starbucks and McDonald's reported stronger same-store sales.")
        self.assertIn("استارباکس", value)
        self.assertIn("مک‌دونالدز", value)
        self.assertIn("فروش شعب هم‌مقایسه", value)
        self.assertNotIn("Starbucks", value)

    def test_industry_terms_are_stabilized(self):
        value = prepare_for_translation("The QSR improved drive-thru throughput and average check.")
        self.assertIn("درایو‌ثرو", value)
        self.assertIn("ظرفیت و سرعت سرویس", value)
        self.assertIn("میانگین مبلغ فاکتور", value)

    def test_common_machine_translation_phrases_are_cleaned(self):
        value = polish_persian("فروش در همان فروشگاه ها افزایش یافت و ترافیک مشتری بهتر شد .")
        self.assertIn("فروش شعب هم‌مقایسه", value)
        self.assertIn("تعداد مراجعه مشتریان", value)
        self.assertNotIn(" .", value)

    def test_arabic_variants_are_normalized(self):
        self.assertEqual(polish_persian("كيفيت غذاي ايراني"), "کیفیت غذای ایرانی")


if __name__ == "__main__":
    unittest.main()
