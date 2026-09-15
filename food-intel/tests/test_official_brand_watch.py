import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from official_brand_watch import _headline, _message_relevant


class OfficialBrandWatchTests(unittest.TestCase):
    def test_padideh_requires_food_context(self):
        channel = {"context": ["رستوران", "فود هال", "کافه"]}
        settings = {"signal_terms": ["افتتاح", "رونمایی", "رستوران"]}
        self.assertFalse(_message_relevant("افتتاح بخش تازه مرکز خرید پدیده", channel, settings))
        self.assertTrue(_message_relevant("رونمایی از امکانات تازه رستوران پدیده شاندیز", channel, settings))

    def test_signal_filter_rejects_generic_social_post(self):
        channel = {}
        settings = {"signal_terms": ["شعبه", "محصول جدید", "همکاری"]}
        self.assertFalse(_message_relevant("امروز کنار شما هستیم و روز خوبی آرزو می‌کنیم", channel, settings))
        self.assertTrue(_message_relevant("شعبه جدید این مجموعه هفته آینده افتتاح می‌شود", channel, settings))

    def test_headline_is_bounded(self):
        text = "رونمایی از منوی تازه رستوران. این بخش توضیح طولانی‌تری درباره برنامه جدید دارد."
        self.assertEqual(_headline(text), "رونمایی از منوی تازه رستوران")


if __name__ == "__main__":
    unittest.main()
