from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "config" / "sources.yml"


class SourceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        payload = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8")) or {}
        cls.sources = payload.get("sources", [])

    def test_source_ids_are_unique(self):
        ids = [source.get("id") for source in self.sources]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn(None, ids)

    def test_enabled_sources_are_rss_with_feed_urls(self):
        enabled = [source for source in self.sources if source.get("enabled")]
        self.assertGreaterEqual(len(enabled), 10)
        for source in enabled:
            self.assertEqual(source.get("type"), "rss", source.get("id"))
            self.assertTrue(source.get("feed_url"), source.get("id"))
            self.assertTrue(source["feed_url"].startswith("https://"), source.get("id"))

    def test_discovery_sources_are_disabled(self):
        for source in self.sources:
            if source.get("type") == "discovery":
                self.assertFalse(source.get("enabled"), source.get("id"))

    def test_priority_values_are_bounded(self):
        for source in self.sources:
            priority = source.get("priority")
            self.assertIn(priority, (1, 2, 3), source.get("id"))

    def test_active_sources_have_verification_date(self):
        for source in self.sources:
            if source.get("enabled"):
                self.assertTrue(source.get("verified_at"), source.get("id"))


if __name__ == "__main__":
    unittest.main()
