import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from score import relevance_score


class ScoreTests(unittest.TestCase):
    def test_priority_and_freshness_raise_score(self):
        now = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
        article = {
            "title": "Restaurant chain adopts AI kitchen automation",
            "summary": "A detailed operations update covering automation, throughput and restaurant technology.",
            "published_at": "2026-09-15T08:00:00Z",
            "categories": ["restaurant_operations", "restaurant_technology_ai"],
            "topics": ["AI", "automation"],
            "source": {"class": "industry_publication", "priority": 1},
        }
        self.assertGreaterEqual(relevance_score(article, now=now), 80)

    def test_score_is_bounded(self):
        article = {"categories": [], "topics": [], "source": {"priority": 9}}
        score = relevance_score(article)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
