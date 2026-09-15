from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from media import entry_image_url


class MediaTests(unittest.TestCase):
    def test_media_content_wins(self):
        entry = SimpleNamespace(
            media_content=[{"url": "https://example.com/hero.jpg", "type": "image/jpeg"}],
            media_thumbnail=[],
            enclosures=[],
            links=[],
            summary="",
            description="",
            content=[],
        )
        self.assertEqual(entry_image_url(entry), "https://example.com/hero.jpg")

    def test_enclosure_image(self):
        entry = SimpleNamespace(
            media_content=[],
            media_thumbnail=[],
            enclosures=[{"href": "https://example.com/photo.webp", "type": "image/webp"}],
            links=[],
            summary="",
            description="",
            content=[],
        )
        self.assertEqual(entry_image_url(entry), "https://example.com/photo.webp")

    def test_embedded_summary_image(self):
        entry = SimpleNamespace(
            media_content=[],
            media_thumbnail=[],
            enclosures=[],
            links=[],
            summary='<p>hello<img src="https://example.com/inside.png"></p>',
            description="",
            content=[],
        )
        self.assertEqual(entry_image_url(entry), "https://example.com/inside.png")

    def test_reject_non_http(self):
        entry = SimpleNamespace(
            media_content=[{"url": "javascript:alert(1)", "type": "image/jpeg"}],
            media_thumbnail=[],
            enclosures=[],
            links=[],
            summary="",
            description="",
            content=[],
        )
        self.assertIsNone(entry_image_url(entry))


if __name__ == "__main__":
    unittest.main()
